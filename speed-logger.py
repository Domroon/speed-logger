import logging
import argparse
import configparser

import speedtest
from sqlalchemy import engine_from_config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, ForeignKey, DateTime, String, Integer, Float
from sqlalchemy.sql import func


config = configparser.ConfigParser()
config.read('config.ini')
log_level = int(config['SETTINGS']['log_level'])
filename = config['SETTINGS']['log_filename']

engine = engine_from_config(config['DATABASE'], prefix='sqlalchemy.')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

logging.basicConfig(filename=filename, format='%(asctime)s %(levelname)s %(message)s', level=log_level)


class MeasureStat(Base):
    __tablename__ = 'measureStat'
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(ForeignKey('server.id'))
    client_id = Column(ForeignKey('client.id'))
    server = relationship("Server")
    client = relationship("Client")
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    download = Column(Float)
    upload = Column(Float)
    ping = Column(Float)
    timestamp = Column(String)
    bytes_sent = Column(Integer)
    bytes_received = Column(Integer)
    share = Column(String)


class Server(Base):
    __tablename__ = 'server'
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    name = Column(String)
    country = Column(String)
    cc = Column(String)
    sponsor = Column(String)
    server_id = Column(Integer)
    host = Column(String)
    d = Column(Float)
    latency = Column(Float)



class Client(Base):
    __tablename__ = 'client'
    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    isp = Column(String)
    isprating = Column(Float)
    rating = Column(Integer)
    ispdlavg = Column(Integer)
    ispulavg = Column(Integer)
    loggedin = Column(Integer)
    country = Column(String)



def test_speed():
    servers = []
    # If you want to test against a specific server
    # servers = [1234]

    threads = None
    # If you want to use a single threaded test
    # threads = 1
    
    s = speedtest.Speedtest()
    logging.debug('Get all available servers')
    s.get_servers(servers)
    logging.debug('Get best server')
    s.get_best_server()
    logging.info('Test download speed')
    s.download(threads=threads)
    logging.info('Test upload speed')
    s.upload(threads=threads)
    s.results.share()
    return s.results.dict()
        

def get_prog_args():
    parser = argparse.ArgumentParser(description='Start a speedtest or show results on localhost website')

    subparsers = parser.add_subparsers(help='sub-commands', dest='sub')
    subparsers.add_parser('start-test', help='Starts a single speedtest')
    subparsers.add_parser('start-server', help='Starts a server on localhost that show the results')
    subparsers.add_parser('show-all', help='Shows all recorded speed tests')
    subparsers.add_parser('create-db', help='Create a SQLite Database and add necessary tables to it')

    return parser.parse_args()


def add_server_data(result_dict):
    with SessionLocal() as db:
        server = Server(
            url = result_dict['url'],
            lat = result_dict['lat'],
            lon = result_dict['lon'],
            name = result_dict['name'],
            country = result_dict['country'],
            cc = result_dict['cc'],
            sponsor = result_dict['sponsor'],
            server_id = result_dict['id'],
            host = result_dict['host'],
            d = result_dict['d'],
            latency = result_dict['latency'],
        )
        db.add(server)
        db.commit()
        db.refresh(server)
        return server.id


def add_client_data(result_dict):
    with SessionLocal() as db:
        client = Client(
            ip = result_dict['ip'],
            lat = result_dict['lat'],
            lon = result_dict['lon'],
            isp = result_dict['isp'],
            isprating = result_dict['isprating'],
            rating = result_dict['rating'],
            ispdlavg = result_dict['ispdlavg'],
            ispulavg = result_dict['ispulavg'],
            loggedin = result_dict['loggedin'],
            country = result_dict['country']
        )
        db.add(client)
        db.commit()
        db.refresh(client)
        return client.id


def add_measureStat_data(result_dict, server_id, client_id):
    with SessionLocal() as db:
        measureStat = MeasureStat(
            server_id = server_id,
            client_id = client_id,
            download = result_dict['download'],
            upload = result_dict['upload'],
            ping = result_dict['ping'],
            timestamp = result_dict['timestamp'],
            bytes_sent = result_dict['bytes_sent'],
            bytes_received = result_dict['bytes_received'],
            share = result_dict['share']
        )
        db.add(measureStat)
        db.commit()
        db.refresh(measureStat)
        return measureStat.id


def main():
    args = get_prog_args()
    if args.sub == 'start-test':
        logging.info('Start speedtest')
        try:
            speed_test_result = test_speed()
        except:
            logging.exception('Can not measure speed')

        try:
            server_id = add_server_data(speed_test_result['server'])
            client_id = add_client_data(speed_test_result['client'])
            measure_id = add_measureStat_data(speed_test_result, server_id, client_id)
            logging.info(f'Store measurement {measure_id}')

        except:
            logging.exception('Can not write to Database')
            
    elif args.sub == 'create-db':
        Base.metadata.create_all(engine)
        logging.info('Create Database')
    elif args.sub == 'show-all':
        with SessionLocal() as db:
            measurements = db.query(MeasureStat).all()
            for m in measurements:
                datetime_utc_offset = m.added_at + m.added_at.astimezone().utcoffset()
                print(f'{m.id} |', f'{datetime_utc_offset} |', f'download: {round(m.download/1000000, 2)} mbit/s |', f'upload: {round(m.upload/1000000, 2)} mbit/s |', f'ping: {m.ping}')
    elif args.sub == 'start-server':
        print('The server will start here')


if __name__ == '__main__':
    main()