#!/usr/bin/env python3
#
# Fedora 4 HTML-UI tests using Selenium-RC.
# Jared Whiklo
# 

import os, sys
import argparse, configparser
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0

# The full hostname, port and path to Fedora instance
fedoraUrl = None
# Logger
logger = None
# Configuration variables
config = None
# Webdriver
driver = None

'''
Nested container test
'''
def nestedContainers():
    if createContainer(None, 'container1'):
        if createContainer('container1', 'container2'):
            logger.info("Created 2 nested containers")
            if not deleteResource(fedoraUrl + '/container1'):
                logger.error("Couldn't delete {}".format(fedoraUrl + '/container1'))
        
'''
Delete a resource
'''
def deleteResource(path):
    path = path.rstrip('/')
    driver.get(path)
    try:
        element = WebDriverWait(driver, 5).until(lambda x :  x.current_url == path);
    except TimeoutException as e:
        logger.error("Waited 10 seconds to move to {} and it didn't happen.".format(path))
        return False
    
    parent = path.rsplit('/',1)[0]
    driver.find_element_by_id('action_delete').find_element_by_name('delete-button').click()
    try:
        element = WebDriverWait(driver, 5).until(lambda x : x.current_url == parent)
    except TimeoutException as e:
        logger.error("Tried to delete {}, page did not respond after 5 seconds.".format(path))
        return False
    return True
    
    
'''
Creates a resource container, with PUT or POST.

Keyword arguments
parent - path to the parent container
ctnName - name for the container
'''
def createContainer(parent = None, ctnName = None):
    path = fedoraUrl.rstrip('/') + '/'
    if parent is not None: 
        path += parent + '/'
    driver.get(path)
    try:
        identifier = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "new_id")))
    except TimeoutException as e:
        logger.error("The home page did not load in 10 seconds, is the URL ({}) correct?".format(fedoraUrl))
        return False
    
    oldPath = driver.current_url
    
    logger.debug('Creating a new container')
    
    if ctnName is not None:
        driver.find_element_by_id('new_id').send_keys(ctnName)
    driver.find_element_by_id('btn_action_create').click()
    
    try:
        element = WebDriverWait(driver, 5).until_not(lambda x :  x.current_url == oldPath);
    except TimeoutException as e:
        logger.error("Waited 10 seconds to create container " + ctnName + ", didn't happen.")
        return False
    
    if ctnName is not None:
        if not driver.find_element_by_id('main').get_attribute('resource') == path + ctnName:
            print("Error ended up on page {} instead of {}".format(driver.title, path + ctnName))
            return False
    return True

'''
Run our tests
'''
def runTests():
    global driver
    # Create a new instance of the Firefox driver
    driver = webdriver.Firefox()
    logIn()
    nestedContainers()
    driver.quit() 

'''
This is the best way to authenticate, using username:password@URL
'''
def logIn():
    if 'username' in config['FEDORA'] and 'password' in config['FEDORA']:
        if len(config['FEDORA']['username']) > 0 and len(config['FEDORA']['password']) > 0:
            (protocol, uri) = fedoraUrl.split('://')
            driver.get(protocol + '://' + config['FEDORA']['username'] + ':' + config['FEDORA']['password'] + '@' + uri)

'''
Load the configuration file and setup the logger

Keyword arguments
configFile - The path to the configuration file
'''
def loadConfig(configFile):
    global fedoraUrl, logger, config
    config = configparser.ConfigParser()
    config.read(configFile)
    if 'FEDORA' in config:
        fedoraUrl = config['FEDORA']['fullUrl'].rstrip('/')
    else:
        print("ERROR: No full Fedora URL defined in configuration file.")
        quit();
    
    if 'LOGGING' in config:
        loggingCfg = config['LOGGING']
        logger = logging.getLogger('F4-HTML')
        logger.propogate = False
        # Logging Level 
        eval('logger.setLevel(logging.{})'.format(loggingCfg.get('level', 'INFO')))
        logfile = loggingCfg.get('logfile', os.path.join(os.path.dirname(__file__), 'F4-HTML.log'))
        if not os.path.exists(os.path.dirname(logfile)):
            response = input("ERROR: Logfile directory {} does not exist, attempt to create it (y/N)?".format(os.path.dirname(logfile)))
            if response.lower() == "y":
                try:
                    os.makedirs(os.path.dirname(logfile))
                except OSError as e:
                    print("ERROR creating directory: {}".format(e.getMessage()))
                    quit()
        fh = logging.FileHandler(logfile, 'w', 'utf-8')
        formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

'''
Main program
''' 
def doMain(arguments):
    loadConfig(args.config)
    runTests()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run a set of Fedora 4 tests against the HTML UI using Selenium.')
    parser.add_argument('-f', '--config', dest="config", default='./html_tester.cfg', help='Configuration file, defaults to ./html_tester.cfg')
    args = parser.parse_args()
    
    if not (os.path.exists(args.config) and os.path.isfile(args.config) and os.access(args.config, os.R_OK)):
        parser.error("{} does not exist, or is not a readable file.".format(args.config))
        
    doMain(args)
