#!/usr/bin/env python
# encoding=utf-8

# def job():
#     print("I'm working...")
#
#
# client = MongoClient(host='127.0.0.1', port=27017)
# mongodb = MongoDBJobStore(client=client)
# jobstores = {
#     'mongodb': MongoDBJobStore(),
#     'default': MemoryJobStore()
# }
# executors = {
#     'default': ThreadPoolExecutor(10),
#     'processpool': ProcessPoolExecutor(3)
# }
# job_defaults = {
#     'coalesce': False,
#     'max_instances': 3
# }
# sched = BlockingScheduler(jobstore=jobstores, executors=executors, job_defaults=job_defaults)
# sched.add_jobstore('mongodb', collection='example_jobs', database='minnie')
# sched.add_job(job, 'cron', day_of_week='mon-fri', hour='8-20', minute="*", second="*/10")
# sched.start()