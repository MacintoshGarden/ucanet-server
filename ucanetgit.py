"""
Unverified
"""
import re
import time
import git
import configparser
import os
from apscheduler.schedulers.background import BackgroundScheduler
from cachetools import TTLCache
from threading import Lock

REGISTRY_PATH = ucaconf.get('LIB_REGISTRY','PATH')
GIT_USERNAME = ucaconf.get('LIB_GIT','USERNAME')
GIT_PASSWORD = ucaconf.get('LIB_GIT','TOKEN')
GIT_URL = ucaconf.get('LIB_GIT','URL')
GIT_BRANCH = ucaconf.get('LIB_GIT','BRANCH')
GIT_PATH = ucaconf.get('LIB_GIT','PATH')

pending_changes = {}
git_scheduler = BackgroundScheduler()
file_lock = Lock()
pending_lock = Lock()

if not os.path.exists(GIT_PATH):
	os.makedirs(GIT_PATH)
	
def is_git_repo(path):
	try:
		_ = git.Repo(path).git_dir
		return True
	except git.exc.InvalidGitRepositoryError:
		return False

def start_git():
	if is_git_repo(GIT_PATH):	
		repo = git.Repo.init(GIT_PATH, initial_branch=GIT_BRANCH)	
		return repo, repo.remote(name='origin')
	else:	
		repo = git.Repo.init(GIT_PATH, initial_branch=GIT_BRANCH)	
		return repo, repo.create_remote('origin', GIT_URL)
		
repo, origin = start_git()
repo.git.add(all=True)

def pull_git():
	file_lock.acquire()
	try:
		origin.pull(GIT_BRANCH)
	except:
		pass
	file_lock.release()
	
def push_git():
	pending_lock.acquire()
	file_lock.acquire()
	if len(pending_changes) > 0:
		try:
			formatted_changes = {}
			
			for user_id, domain_list in pending_changes.items():
				for current_name, current_ip in domain_list.items():
					formatted_changes[current_name] = f'{current_name} {user_id} {current_ip}' + "\n"
			
			with open(REGISTRY_PATH, 'r') as registry_file:
				registry_lines = registry_file.readlines()
				
			line_count = 0
			
			for line in registry_lines:
				split_lines = line.strip().split(' ')
				
				if split_lines[0] in formatted_changes:
					registry_lines[line_count] = formatted_changes[split_lines[0]]
					del formatted_changes[split_lines[0]]
					
				line_count += 1
			
			for current_name, formatted_change in formatted_changes.items():
				if len(registry_lines) > 0:
					registry_lines[-1] = registry_lines[-1].replace("\n", "")
					registry_lines[-1] = registry_lines[-1] + "\n"
				registry_lines.append(formatted_change)
			
			if len(registry_lines) > 0:
				registry_lines[-1] = registry_lines[-1].replace("\n", "")
				
			with open(REGISTRY_PATH, 'w') as registry_file:
				registry_file.writelines(registry_lines)
				
			pending_changes.clear()
		except:
			pass
		
		try:
			repo = git.Repo(GIT_PATH)
			repo.git.add(all=True)
			repo.index.commit("[automated] update registry")
			repo.git.push('--set-upstream', repo.remote().name, GIT_BRANCH)
		except:
			pass
			
	file_lock.release()
	pending_lock.release()

def schedule_git():
	git_scheduler.add_job(id='git-pull-task', func=pull_git, trigger='interval', seconds=600)
	git_scheduler.add_job(id='git-push-task', func=push_git, trigger='interval', seconds=15)
	git_scheduler.start()
	
pull_git()
schedule_git()