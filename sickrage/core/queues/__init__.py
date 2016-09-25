# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

try:
    from Queue import PriorityQueue, Empty
except ImportError:
    from queue import PriorityQueue, Empty

import threading
from datetime import datetime

import sickrage


class srQueuePriorities(object):
    LOW = 10
    NORMAL = 20
    HIGH = 30


class srQueue(threading.Thread):
    def __init__(self, name="QUEUE"):
        super(srQueue, self).__init__(name=name)
        self.queue_name = name
        self._queue = PriorityQueue()
        self.currentItem = None
        self.min_priority = 0
        self.amActive = False
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.daemon = True

    def run(self):
        """
        Process items in this queue
        """

        while not self.stop.is_set():
            with self.lock:
                self.amActive = True

                if self.currentItem is None or not self.currentItem.inProgress:
                    if self.currentItem:
                        self.currentItem = None

                    self.currentItem = self.get()
                    if self.currentItem.priority < self.min_priority:
                        self.put(self.currentItem)
                        self.currentItem = None
                    else:
                        try:
                            threading.currentThread().setName(self.currentItem.name)
                            self.currentItem.run()
                        finally:
                            threading.currentThread().setName(self.queue_name)
                            self.currentItem.finish()

                self.amActive = False

    @property
    def queue(self):
        return self._queue.queue

    def get(self, *args, **kwargs):
        _, item = self._queue.get(*args, **kwargs)
        return item

    def put(self, item, *args, **kwargs):
        """
        Adds an item to this queue

        :param item: Queue object to add
        :return: item
        """
        item.name = "{}-{}".format(self.name, item.name)
        item.added = datetime.now()
        self._queue.put((item.priority, item), *args, **kwargs)
        return item

    def pause(self):
        """Pauses this queue"""
        sickrage.srCore.srLogger.info("Pausing queue")
        self.min_priority = 999999999999

    def unpause(self):
        """Unpauses this queue"""
        sickrage.srCore.srLogger.info("Unpausing queue")
        self.min_priority = 0

    def shutdown(self):
        self.stop.set()
        self.join(10)


class srQueueItem(object):
    def __init__(self, name, action_id=0):
        self.lock = threading.Lock()
        self.name = name.replace(" ", "-").upper()
        self.inProgress = False
        self.priority = srQueuePriorities.NORMAL
        self.action_id = action_id
        self.stop = threading.Event()
        self.added = None

    def run(self):
        self.inProgress = True

    def finish(self):
        self.inProgress = False
