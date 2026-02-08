from configparser import ConfigParser

class ConfParser:
    """Configuration File Parser"""

    def __init__(self, path: str, encode: str='UTF8'):
        self.path = path
        self.encode = encode
        self.parser = ConfigParser()

    def read_any(self, section: str=None, option: str=None) -> str:
        """Read any of section, option, value"""
        self.parser.read(self.path, encoding=self.encode)
        if section is None:
            return self.parser.sections()
        if section in self.parser and option is None:
            return self.parser.options(section)
        if section in self.parser and option in self.parser[section]:
            return self.parser[section][option]
        return None 

    def read_as_dict(self, section: str=None) -> dict:
        """Read as dict"""
        configs = {}
        self.parser.read(self.path, encoding=self.encode)
        if section is None:
            for section in self.parser.sections():
                configs[section] = {}
                for option, value in self.parser.items(section):
                    configs[section][option] = value
            return configs
        if section in self.parser.sections():
            for option, value in self.parser.items(section):
                configs[option] = value
            return configs
        return None
            

    def write_one(self, section: str, option: str, value: str) -> None:
        """Write one specified section, option, value"""
        if not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, option, value)
        with open(self.path, 'w', encoding=self.encode) as file:
            self.parser.write(file)

    def delete_one(self, section: str, option: str) -> None:
        """Delete one specified section, option"""
        self.parser.remove_option(section, option)
        if self.readoptions(section) == []:
            self.parser.remove_section(section)
        with open(self.path, 'w', encoding=self.encode) as file:
            self.parser.write(file)
        
if __name__ == '__main__':
    cp_o = ConfParser(path='/root/this/svc/edge.ini')
    res = cp_o.read_as_dict('Services')
    print(res)