# :woman_technologist: Development guidelines

## :memo: Commit Messages

### Format
`<type>: <brief description>`

### Types:

`feat`: New Feature

`fix`: Bug fix

`docs`: Documentation

`refactor`: Code-refactoring

`test`: Tests

`chore`: Maintenance, Dependencies etc.

### Example:

feat: add generic painting of extensive sizes

fix: Resolve CI/CD Pipeline problems

docs: update README

test: Add test for pytest mpl plugin

chore: Delete old scripts

## :computer: Logging

Please do **not** use `print()`, since it is unstructured and most of the time chaotic.  
At the beginning of the most scripts there is a method which creates a logger, that can write messages into a logfile. Every message follows a certain structure there that one can afterwards understand what and in which line it was printed. Furthermore the terminal stays, hopefully, clean. The set_up_logger method looks like this:

```Python
def set_up_logger(name,log_dir = None,level=int(logging.ERROR)):
        logger = logging.getLogger(name)
        logger.setLevel(level)

        if log_dir == None:
            log_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
        print(f"Logfile findable here: {log_file}")
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger
```
The method returns a logger that writes a log file. Its used like:

```Python
        self.uesgraph = uesgraph
        self.logger = set_up_logger("Visuals",level=log_level)
        self.logger.info("Visuals object created")
```
After those lines you can always write messages to the log file by typing:

```Python
self.logger.info("..")
#or
self.logger.debug("..")
```
For further informations about the logging module consult the [documentation](https://docs.python.org/3/library/logging.html)



## :white_check_mark: Testing

- Run test before Commit
- Pytest test should pass or have to be modified

## :art: Code style

- Conventions are always a good idea: [PEP 8](https://peps.python.org/pep-0008/)
