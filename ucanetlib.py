import re
import tldextract
import time
import os
import configparser
import sqlite3
from ipaddress import ip_address, IPv4Address
from cachetools import TTLCache
from threading import Lock

CACHE_SIZE = int(ucaconf.get('LIB_CACHE','SIZE'))
CACHE_TTL = int(ucaconf.get('LIB_CACHE','TTL'))

# Dirty old fix since we most likely won't be in the same thread at all when calling the db
# This could probably be remedied if we moved this down to each method and removed the check
#con = sqlite3.connect("ucanet-registry.db", check_same_thread=False)
con = sqlite3.connect(":memory:", check_same_thread=False)
cur = con.cursor()

sql_file = open("ucanet-registry.sql")
sql_as_string = sql_file.read()
cur.executescript(sql_as_string)

pending_changes = {}
entry_cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL)
offline_extract = tldextract.TLDExtract(suffix_list_urls=())
entry_lock = Lock()
pending_lock = Lock()

def format_domain(domain_name):
	domain_name = domain_name.lower()
	if len(domain_name) > 255:
		return False
	if domain_name[-1] == ".":
		domain_name = domain_name[:-1]
	allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
	if all(allowed.match(x) for x in domain_name.split(".")):
		extracted = offline_extract(domain_name)
		if len(extracted.domain) > 0 and len(extracted.suffix) > 0:
			return domain_name
	return False

def format_ip(current_ip):
	if current_ip == "none":
		return "0.0.0.0"
	try:
		return current_ip if type(ip_address(current_ip)) is IPv4Address else False
	except ValueError:
		return False

def second_level(domain_name):
	domain_name = format_domain(domain_name)

	if domain_name:
		extracted = offline_extract(domain_name)

		if len(extracted.subdomain) > 0:
			return "{}.{}".format(extracted.domain, extracted.suffix)

	return False

def find_pending(domain_name):
	pending_lock.acquire()
	for user_id, domain_list in pending_changes.items():
		for current_name, current_ip in domain_list.items():
			if current_name == domain_name:
				pending_lock.release()
				return current_ip
	pending_lock.release()
	return False

def find_entry(domain_name):
	if not domain_name:
		return False

	domain_name = format_domain(domain_name)
	if found_pending := find_pending(domain_name):
		return found_pending

	entry_lock.acquire()
	if domain_name in entry_cache.keys():
		entry_lock.release()
		return entry_cache[domain_name]
	entry_lock.release()

	if domain_name:
		cur.execute('SELECT name, address FROM registry')
		res = cur.fetchall()

		for registry in res:
				if registry[0] == domain_name:
						entry_lock.acquire()
						entry_cache[domain_name] = registry[1]
						entry_lock.release()
						return registry[1]

		if entry := find_entry(second_level(domain_name)):
			entry_lock.acquire()
			entry_cache[domain_name] = entry
			entry_lock.release()
			return entry

	return False

def user_domains(user_id):
	domain_list = {}

	cur.execute('SELECT name, uid, address FROM registry WHERE uid=?',user_id)
	res = cur.fetchall

	for line in res:
			if int(line[1]) == user_id:
					domain_list[line[0]] = line[2]

	pending_lock.acquire()
	if user_id in pending_changes.keys():
		for domain_name, current_ip in pending_changes[user_id].items():
			domain_list[domain_name] = current_ip
	pending_lock.release()

	return domain_list

def register_domain(domain_name, user_id):
	domain_list = user_domains(user_id)
	if len(domain_list) >= 20:
		return False
	pending_lock.acquire()
	if user_id not in pending_changes.keys():
		pending_changes[user_id] = {}
	pending_changes[user_id][domain_name] = "0.0.0.0"
	pending_lock.release()
	print(f'{domain_name} registered by {user_id}')
	return True

def register_ip(domain_name, user_id, current_ip):
	domain_list = user_domains(user_id)
	if len(domain_list) >= 20 and domain_name not in domain_list:
		return False
	pending_lock.acquire()
	if user_id not in pending_changes.keys():
		pending_changes[user_id] = {}
	pending_changes[user_id][domain_name] = current_ip
	pending_lock.release()
	print(f'{domain_name} set ip to {current_ip} by {user_id}')
	return True