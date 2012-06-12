# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from fabric.api import run, env, sudo
from fabric.context_managers import cd, settings
import os
from datetime import date

PROJECT_DIR = os.path.dirname(__file__)


def git_clone_datawinners_if_not_present(code_dir):
    if run("test -d %s" % code_dir).failed:
        run("git clone git://github.com/mangroveorg/datawinners.git %s" % code_dir)
        
def git_clone_mangrove_if_not_present(code_dir):
    if run("test -d %s" % code_dir).failed:
        run("git clone git://github.com/mangroveorg/mangrove.git %s" % code_dir)

def activate_and_run(virtual_env, command):
    run('source %s/bin/activate && ' % virtual_env + command)


def branch_exists(branch_name):
    return not run("git branch -a|grep %s" % branch_name).failed


def sync_branch(branch):
    run("git checkout %s" % branch)
    run("git pull origin %s" % branch)


def delete_if_branch_exists(build_number):
    if branch_exists(build_number):
        run("git branch -D %s" % build_number)


def restart_gunicorn(virtual_env):
    if gunicorn_is_running():
        stop_gunicorn()
    start_gunicorn(virtual_env)


def gunicorn_is_running():
    return not run("pgrep gunicorn").failed


def stop_gunicorn():
    run("kill -9 `pgrep gunicorn`")


def start_gunicorn(virtual_env):
    activate_and_run(virtual_env, "gunicorn_django -D -b 0.0.0.0:8000 --pid=mangrove_gunicorn")


def restart_servers():
    stop_servers()
    start_servers()


def stop_servers():
    run("sudo service uwsgi stop, pty=False")
    run("sudo service nginx stop, pty=False")


def start_servers():
    run("sudo service uwsgi start, pty=False")
    run("sudo service nginx start, pty=False")


def set_mangrove_commit_sha(branch, mangrove_build_number):
    if mangrove_build_number == 'lastSuccessfulBuild':
        mangrove_build_number = run(
            "curl http://178.79.163.33:8080/job/Mangrove-%s/lastSuccessfulBuild/buildNumber" % (branch,))
    run(
        "export MANGROVE_COMMIT_SHA=`curl http://178.79.163.33:8080/job/Mangrove-%s/%s/artifact/last_successful_commit_sha`" % (
            branch, mangrove_build_number))
    
def set_datawinner_commit_sha(datawinner_build_number):
    if datawinner_build_number == 'lastSuccessfulBuild':
        datawinner_build_number = run(
            "curl http://178.79.163.33:8080/job/Datawinners/lastSuccessfulBuild/buildNumber")
    run(
        "export DATWINNER_COMMIT_SHA=`curl http://178.79.163.33:8080/job/Datawinners/%s/artifact/last_successful_commit_sha`" % (
            datawinner_build_number))

def check_out_mangrove_code(mangrove_build_number, mangrove_code_dir, branch, virtual_env):
    git_clone_mangrove_if_not_present(mangrove_code_dir)
    with cd(mangrove_code_dir):
        run("cd %s" % mangrove_code_dir)
        run("git reset --hard HEAD")
        sync_branch(branch)
        delete_if_branch_exists(mangrove_build_number)
        run("git checkout -b %s $MANGROVE_COMMIT_SHA" % (mangrove_build_number, ))
        run("git checkout .")
        activate_and_run(virtual_env, "pip install -r requirements.pip")
        activate_and_run(virtual_env, "python setup.py develop")
        
def check_out_datawinners_code(datawinner_build_number, datawinners_code_dir, virtual_env):
    git_clone_datawinners_if_not_present(datawinners_code_dir)
    with cd(datawinners_code_dir):
        run("cd %s" % datawinners_code_dir)
        run("git reset --hard HEAD")
        sync_branch("develop")
        delete_if_branch_exists(datawinner_build_number)
        run("git checkout -b %s $DATAWINNER_COMMIT_SHA" % (datawinner_build_number, ))
        run("git checkout .")
        activate_and_run(virtual_env, "pip install -r requirements.pip")

def deploy(mangrove_build_number, datawinner_build_number, home_dir, virtual_env, branch="develop", environment="showcase"):
    """build_number : hudson build number to be deployed
       home_dir: directory where you want to deploy the source code
       virtual_env : path to your virtual_env folder
    """

    set_mangrove_commit_sha(branch, mangrove_build_number)
    set_datawinner_commit_sha(datawinner_build_number)

    ENVIRONMENT_CONFIGURATIONS = {
        "showcase": "showcase_local_settings.py",
        "test": "test_local_settings.py",
        "master": "showcase_local_settings.py",
        "beta": "local_settings.py"
    }

    mangrove_code_dir = home_dir + '/mangrove'
    datawinners_code_dir = home_dir + '/datawinners'
    with settings(warn_only=True):
        check_out_mangrove_code(mangrove_build_number, mangrove_code_dir, branch, virtual_env)
        check_out_datawinners_code(datawinner_build_number, datawinners_code_dir, virtual_env)
        with cd(datawinners_code_dir + '/datawinners'):
            run("cd %s/datawinners" % datawinners_code_dir)
            run("cp %s local_settings.py" % (ENVIRONMENT_CONFIGURATIONS[environment],))
            activate_and_run(virtual_env, "python manage.py syncdb --noinput")
            activate_and_run(virtual_env, "python manage.py migrate")
            activate_and_run(virtual_env, "python manage.py recreatedb")
            activate_and_run(virtual_env, "python manage.py compilemessages")
            if environment == "test":
                restart_gunicorn(virtual_env)
            else:
                restart_servers()

def killfirefox():
    with settings(warn_only=True):
        run("killall firefox")

def showcase():
    env.user = "mangrover"
    env.hosts = ["178.79.161.90"]
    env.key_filename = ["/var/lib/jenkins/.ssh/id_rsa"]

def local():
    env.user = "mangrover"
    env.hosts = ["127.0.0.1"]
    env.key_filename = ["/var/lib/jenkins/.ssh/id_rsa"]

def production():
    env.user = "mangrover"
    env.hosts = ["178.79.185.34"]
    env.key_filename = ["/var/lib/jenkins/.ssh/id_rsa"]
    env.warn_only = True

def test2():
    env.user = "ashwini"
    env.hosts = ["10.12.6.29"]
    env.key_filename = ["/home/akshaysn/.ssh/id_rsa"]
    env.warn_only = True

def anonymous():
    run("uname -a")

def checkout_mangrove_to_production(code_dir, virtual_env):
    if run("cd %s && ls | grep mangrove" % code_dir).failed:
        run('cd %s && git clone git://github.com/mangroveorg/mangrove.git' % code_dir)
    mangrove_dir = code_dir + '/mangrove'
    with cd(mangrove_dir):
        run("git reset --hard HEAD")
        run("git checkout develop")
        run("git pull origin develop")
        mangrove_branch = str(date.today()).replace('-', '')
        if run("git branch -a|grep %s" % mangrove_branch).succeeded:
            run("git branch -D %s" % mangrove_branch)
        run("git checkout -b %s $MANGROVE_COMMIT_SHA" % mangrove_branch)
        run("git checkout .")
        activate_and_run(virtual_env, "pip install -r requirements.pip")
        activate_and_run(virtual_env, "python setup.py develop")

def check_out_datawinners_code_for_production(code_dir, virtual_env):
    if run("cd %s && ls | grep datawinners" % code_dir).failed:
        run('cd %s && git clone git://github.com/mangroveorg/datawinners.git' % code_dir)
    datawinners_dir = code_dir + '/datawinners'
    with cd(datawinners_dir):
        run("git reset --hard HEAD")
        run("git checkout develop")
        run("git pull origin develop")
        datawinner_branch = str(date.today()).replace('-', '')
        if run("git branch -a|grep %s" % datawinner_branch).succeeded:
            run("git branch -D %s" % datawinner_branch)
        run("git checkout -b %s $DATAWINNER_COMMIT_SHA" % datawinner_branch)
        run("git checkout .")
        activate_and_run(virtual_env, "pip install -r requirements.pip")

def production_deploy(mangrove_build_number, datawinner_build_number, code_dir, virtual_env, couch_migration_file=None):
    run('sudo /etc/init.d/nginx stop')
    run('sudo /etc/init.d/uwsgi stop')

    set_mangrove_commit_sha('develop', mangrove_build_number)
    set_datawinner_commit_sha(datawinner_build_number)

    checkout_mangrove_to_production(code_dir, virtual_env)
    check_out_datawinners_code_for_production(code_dir, virtual_env)

    datawinners_dir = code_dir + '/datawinners/datawinners'
    with cd(datawinners_dir):
        run("cp prod_local_settings.py local_settings.py")
        activate_and_run(virtual_env, "python manage.py migrate")
        activate_and_run(virtual_env, "python manage.py compilemessages")
        activate_and_run(virtual_env, "python manage.py syncviews syncall")

    if couch_migration_file is not None:
        with cd('%s/datawinners' % code_dir):
            activate_and_run(virtual_env, "python %s" % couch_migration_file)

    if run('cd mangrove').succeeded:
        run('rm -rf mangrove')
    run('ln -s %s/mangrove/ mangrove' % code_dir)

    if run('cd datawinners').succeeded:
        run('rm -rf datawinners')
    run('ln -s %s/datawinners/ datawinners' % code_dir)

    run('sudo /etc/init.d/nginx start')
    run('sudo /etc/init.d/uwsgi start')
