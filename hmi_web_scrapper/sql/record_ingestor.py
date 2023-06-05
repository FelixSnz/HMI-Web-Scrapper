import os
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sql.db_manager import DBManager

from sql.config import host, database, user, password

from utils.logger import get_logger

class CsvFileHandler(FileSystemEventHandler):
    def __init__(self, db_manager):
        self.db_manager:DBManager = db_manager
        self.logger = get_logger(__name__, self.__class__.__name__)

    def on_created(self, event):
        if event.is_directory:
            self.logger.warn(f"Directory created: {event.src_path}")
        if not event.src_path.lower().endswith('.csv'):
            self.logger.warn(f"Unexpected file type: {event.src_path}")

        try:
            df = pd.read_csv(event.src_path)
        except Exception as e:
            self.logger.error(f"Couldn't read new file: '{event.src_path}'")
            
        if "E_Standard" not in df.columns:
            self.logger.error(f"Error: 'E_Standard' column not found in file {event.src_path}")
            return

        for _, row in df.iterrows():
            try:
                table = row['E_Standard']
                data = row.drop('E_Standard').tolist()
                self.db_manager.insert(table, data)
            except Exception as e:
                self.logger.error(f"Error while inserting csv data: {e}")
            finally:
                self.logger.debug(f"data: {data} inserted at {host}:{database}:{table}")
                self.logger.debug(f"{self.db_manager.__get_column_names(table)}")



class RecordIngestor:
    def __init__(self, path):
        self.path = path

        self.db_manager = DBManager(
            server=host,
            database=database,
            user=user,
            password=password
        )
        
        self.db_manager.connect()
        

    def start(self):
        event_handler = CsvFileHandler(self.db_manager)
        observer = Observer()
        observer.schedule(event_handler, self.path, recursive=False)
        observer.start()

        try:
            while True:
                pass
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

        self.db_manager.disconnect()