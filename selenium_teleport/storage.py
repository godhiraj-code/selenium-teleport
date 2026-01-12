"""
Selenium Teleport - Storage Module

Functions for extracting and injecting browser storage (localStorage, sessionStorage, IndexedDB).
"""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def get_local_storage(driver) -> Dict[str, Any]:
    """
    Extract localStorage from the browser.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        Dictionary of localStorage key-value pairs
    """
    return _get_storage(driver, "localStorage")


def get_session_storage(driver) -> Dict[str, Any]:
    """
    Extract sessionStorage from the browser.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        Dictionary of sessionStorage key-value pairs
    """
    return _get_storage(driver, "sessionStorage")


def _get_storage(driver, storage_type: str) -> Dict[str, Any]:
    """Extract localStorage or sessionStorage from the browser."""
    try:
        script = f"""
            var storage = window.{storage_type};
            var data = {{}};
            for (var i = 0; i < storage.length; i++) {{
                var key = storage.key(i);
                data[key] = storage.getItem(key);
            }}
            return data;
        """
        return driver.execute_script(script) or {}
    except Exception as e:
        logger.warning(f"Failed to extract {storage_type}: {e}")
        return {}


def set_local_storage(driver, data: Dict[str, Any]) -> None:
    """
    Inject data into localStorage.

    Args:
        driver: Selenium WebDriver instance
        data: Dictionary of key-value pairs to inject
    """
    _set_storage(driver, "localStorage", data)


def set_session_storage(driver, data: Dict[str, Any]) -> None:
    """
    Inject data into sessionStorage.

    Args:
        driver: Selenium WebDriver instance
        data: Dictionary of key-value pairs to inject
    """
    _set_storage(driver, "sessionStorage", data)


def _set_storage(driver, storage_type: str, data: Dict[str, Any]) -> None:
    """Inject data into localStorage or sessionStorage."""
    if not data:
        return

    try:
        for key, value in data.items():
            escaped_value = json.dumps(value)
            script = f"window.{storage_type}.setItem({json.dumps(key)}, {escaped_value});"
            driver.execute_script(script)
        logger.debug(f"Injected {len(data)} items into {storage_type}")
    except Exception as e:
        logger.warning(f"Failed to inject {storage_type}: {e}")


def get_indexeddb_info(driver) -> Dict[str, Any]:
    """
    Extract IndexedDB database information from the browser.

    This captures database names and object store names used by modern web apps.
    Note: Full data extraction is not performed due to complexity.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        Dictionary with database names as keys and info as values
    """
    try:
        script = """
            return new Promise((resolve) => {
                const dbData = {};
                
                if (!window.indexedDB) {
                    resolve(dbData);
                    return;
                }
                
                // Get list of databases
                if (indexedDB.databases) {
                    indexedDB.databases().then(databases => {
                        if (databases.length === 0) {
                            resolve(dbData);
                            return;
                        }
                        
                        let completed = 0;
                        databases.forEach(dbInfo => {
                            const dbName = dbInfo.name;
                            const request = indexedDB.open(dbName);
                            
                            request.onerror = () => {
                                completed++;
                                if (completed === databases.length) resolve(dbData);
                            };
                            
                            request.onsuccess = (event) => {
                                const db = event.target.result;
                                dbData[dbName] = {
                                    version: db.version,
                                    stores: Array.from(db.objectStoreNames)
                                };
                                db.close();
                                completed++;
                                if (completed === databases.length) resolve(dbData);
                            };
                        });
                    }).catch(() => resolve(dbData));
                } else {
                    resolve(dbData);
                }
            });
        """
        result = driver.execute_script(script)
        return result if result else {}
    except Exception as e:
        logger.debug(f"IndexedDB extraction not available: {e}")
        return {}


def clear_storage(driver, storage_type: str = "all") -> None:
    """
    Clear browser storage.

    Args:
        driver: Selenium WebDriver instance
        storage_type: "localStorage", "sessionStorage", or "all"
    """
    try:
        if storage_type in ("localStorage", "all"):
            driver.execute_script("localStorage.clear();")
            logger.debug("Cleared localStorage")

        if storage_type in ("sessionStorage", "all"):
            driver.execute_script("sessionStorage.clear();")
            logger.debug("Cleared sessionStorage")
    except Exception as e:
        logger.warning(f"Failed to clear storage: {e}")
