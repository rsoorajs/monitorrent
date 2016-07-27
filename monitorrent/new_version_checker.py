from threading import Timer, RLock
import monitorrent
import requests
import semver


class NewVersionChecker(object):
    releases_url = 'https://api.github.com/repos/werwolfby/monitorrent/releases'
    tagged_release_url = 'https://github.com/werwolfby/monitorrent/releases/tag/{0}'

    def __init__(self, include_prereleases):
        self.include_prereleases = include_prereleases
        self.new_version_url = None
        self.timer = None
        self.stoped = True
        self.update_timer_lock = RLock()

    def start(self, interval):
        if self.timer is not None:
            raise Exception("Stop previous interval before start a new one")
        self.timer = Timer(interval, lambda: self.execute_timer(interval))
        self.timer.start()
        self.stoped = False

    def stop(self):
        with self.update_timer_lock:
            self.stoped = True
            if self.timer is not None:
                self.timer.cancel()
                self.timer = None

    def execute_timer(self, interval):
        try:
            self.execute()
        finally:
            with self.update_timer_lock:
                self.timer = None
                if not self.stoped:
                    self.start(interval)

    def execute(self):
        latest_release = self.get_latest_release()
        monitorrent_version = monitorrent.__version__
        if semver.compare(latest_release, monitorrent_version) > 0:
            self.new_version_url = self.tagged_release_url.format(latest_release)

    def get_latest_release(self):
        response = requests.get(self.releases_url)
        releases = response.json()

        latest_version = None
        for r in releases:
            if r['prerelease'] and not self.include_prereleases:
                continue
            version = r['tag_name']
            # some tag was create with 'v' letter, we should remove it (ex. v0.0.3-alpha -> 0.0.3-alpha)
            if version[0] == 'v':
                version = version[1:]
            if latest_version is None or semver.compare(version, latest_version) > 0:
                latest_version = version
        return latest_version
