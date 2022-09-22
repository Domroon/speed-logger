# speed-logger
![speed-logger](https://user-images.githubusercontent.com/48067330/191795558-fd31c960-5460-4024-9ee2-376797007c58.jpg)

## Installation
    pip install speedtest-cli sqlalchemy
    
## Usage
1. Create database

    python speed-logger.py create-db
    
2. Start a test

    python speed-logger.py start-test
    
Then you can get various information about your measurement
    python speed-logger.py show-all
    python speed-logger.py client-details 1
    python speed-logger.py server-details 1
