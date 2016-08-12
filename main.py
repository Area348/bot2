from commands import create_updater
import logging
import Updates
import time
import threading

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s, %(lineno)s', level=logging.DEBUG)


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._mystop = threading.Event()

    def stop(self):
        self._mystop.set()

    def stopped(self):
        return self._mystop.isSet()

    def run(self):
        logging.debug('5min uodate thread started')
        updater = Updates.get_updates()
        while not self.stopped():
            try:
                updater.update()
            except Exception as e:
                logging.error('update error:  ' + str(e))
                updater.error(e, 'update_thread')
            i = 0
            while i < 300 and not self.stopped():
                di = 5
                time.sleep(di)
        logging.debug('5min update thread stopped')


def main():
    updater = create_updater()
    t = StoppableThread()
    t.start()
    updater.start_polling()
    updater.idle()
    t.stop()
    updates = Updates.get_updates()
    updates.error(Exception("de bot gaat stoppen"), "de bot gaat stoppen")
    t.join()

if __name__ == "__main__":
    main()
