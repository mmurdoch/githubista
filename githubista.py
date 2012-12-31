import console
import keychain
import editor
import os
import base64
from github import Github

def get_password_from_console(username):
	print "Enter password for user", username
	return console.secure_input()

def print_progress_to_console(message):
	print message

get_password_for = get_password_from_console
print_progress = print_progress_to_console

def login(username):
	return Github(username, get_github_password(username)).get_user()

def get_current_repository_name(): # TODO Change this to look for .git directory instead
	current_file = editor.get_path()
	repository_name = None
	tail = ''
	head = current_file
	while tail != '.github':
		repository_name = tail
		head, tail = os.path.split(head)
		if head == '/':
			return None
			
	return repository_name

def get_current_repository(user):
	repository_name = get_current_repository_name()
	return user.get_repo(repository_name)

def clone_repository(user, repository_name, branch_name = 'master'):
	pythonista_dir = os.getcwd()
	github_root_dir = create_directory_if_missing(pythonista_dir, '.github')
	repository_dir = create_directory_if_missing(github_root_dir, repository_name)
	git_dir = create_directory_if_missing(repository_dir, '.git')

	head_file = os.path.join(git_dir, 'HEAD')
	head_ref = 'ref: ' + get_branch_head_ref_name(branch_name)

	with open(head_file, 'w') as head_file_descriptor:
		head_file_descriptor.write(head_ref)
	read_ref(head_file) # TODO Remove
	repository = user.get_repo(repository_name)
	branch_head_commit = get_branch_head_commit(user, repository, branch_name)
	clone_commit(repository, repository_dir, branch_head_commit)

def get_current_head_commit(user):
	repository_name = get_current_repository_name()
	branch_name = get_current_branch_name()
	repository = user.get_repo(repository_name)
	return get_branch_head_commit(user, repository, branch_name)

def get_current_branch_name():
	previous_dir = ''
	current_dir = editor.get_path()
	git_dir_name = '.git'
	git_dir = os.path.join(current_dir, git_dir_name)
	while not os.path.isdir(git_dir):
		previous_dir = current_dir
		current_dir = os.path.split(current_dir)[0]
		print 'previous:', previous_dir
		print 'current:', current_dir
		if current_dir == previous_dir:
			return None
		git_dir = os.path.join(current_dir, git_dir_name)

	head_file = os.path.join(git_dir, 'HEAD')
	head_ref = read_ref(head_file)

	return head_ref.split('/').pop()

def read_ref(ref_file):
	ref = ''
	with open(ref_file, 'r') as ref_file_descriptor:
		ref = ref_file_descriptor.read()
	
	print 'Found', ref, 'in', ref_file
	return ref

def get_branch_head_commit(user, repository, branch_name):
	branch_head_ref = get_branch_head_ref(repository, branch_name)
	return repository.get_git_commit(branch_head_ref.object.sha)

def get_branch_head_ref_name(branch_name):
	return 'refs/heads/' + branch_name

def get_branch_head_ref(repository, branch_name):
	branch_head_ref = None

	for ref in repository.get_git_refs():
		if ref.ref.startswith(get_branch_head_ref_name(branch_name)):
			branch_head_ref = ref

	return branch_head_ref

def create_directory_if_missing(parent_absolute_dir_name, dir_name):
	absolute_dir_name = os.path.join(parent_absolute_dir_name, dir_name)
	try:
		os.mkdir(absolute_dir_name)
	except OSError:
		pass
		
	return absolute_dir_name

def clone_commit(repository, repository_dir, commit):
	head_tree = commit.tree
	tree = repository.get_git_tree(head_tree.sha, True)
	save_recursive_tree(repository, repository_dir, tree.tree)

def save_recursive_tree(repository, repository_dir, tree):
	for element in tree:
		print_progress(element.path)
		save_element(repository, repository_dir, element)

def save_element(repository, repository_dir, element):
	if element.type == 'blob':
		blob = repository.get_git_blob(element.sha)
		content = ''
		if blob.encoding == 'base64':
			content = base64.b64decode(blob.content)
		else:
			raise Exception('Unknown encoding: ' + blob.encoding)

		blob_file = os.path.join(repository_dir, element.path)
		with open(blob_file, 'w') as blob_file_descriptor:
			blob_file_descriptor.write(content)
	elif element.type == 'tree':
		create_directory_if_missing(repository_dir, element.path)

def get_keychain_service():
	return 'github'

def forget_password_for(username):
	keychain.delete_password(get_keychain_service(), username)

def get_github_password(username):
	service = get_keychain_service()
	password = keychain.get_password(service, username)
	if password == None:
		password = get_password_for(username)
		keychain.set_password(service, username, password)
	return password