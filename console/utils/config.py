import sys
import json
import os

class Config(object):
    def __init__(self):
        self.conf = {
                "card-location": None,
                "image-location": None,
                "default-deck-dir": ".",
                }

        if os.path.isdir(os.path.expanduser('~') + "/.config"):
            self.config_dir = os.path.expanduser('~') + "/.config/netrunner-console"
        else:
            self.config_dir = os.path.expanduser('~') + "/.netrunner-console"

        self.config_file = self.config_dir + "/harmlessfile.json"

        if not os.path.exists(self.config_dir):
            os.mkdir(self.config_dir)
        else:
            try:
                with open(self.config_file, "r") as f:
                    loaded = json.load(f)
                    self.conf.update(loaded)
            except FileNotFoundError:
                pass

        self.conf['card-location'] = self.config_dir

    def get(self, key):
        return self.conf.get(key, None)

    def set(self, key, value):
        self.conf[key] = value
       
    def save(self):
       with open(self.config_file, "w") as f:
           json.dump(self.conf, f)

    def load(self):
        loaded = json.load(self.config_file)
        self.conf.update(loaded)
        

if __name__ == "__main__":
    conf = Config()
    print(conf.get('default-deck-dir'))
    print(conf.get('deck-window'))
    print(conf.get('card-location'))
    conf.set("deck-window", "True")

    conf.save()

