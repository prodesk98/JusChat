from workers.tasks import update_knowledge_base


update_knowledge_base.delay('state_of_the_union.txt')
