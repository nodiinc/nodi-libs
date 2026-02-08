from confluent_kafka import Producer, Consumer, TopicPartition
from confluent_kafka.admin import AdminClient, NewTopic, ConfigResource
from collections import deque
from time import sleep, time

class KafkaClient:
    """Kafka Client"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 9092):
        
        # Create client common configs
        self.broker_url = f'{host}:{port}'
        self.client_configs = {'bootstrap.servers': self.broker_url}

    def handle_exception(self, exc):
        """Custom exception handler"""
        
        # Handle exception
        print(exc)

class KafkaProducer(KafkaClient):
    """Kafka Producer"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 9092,
                 client_id: str = 'nodi-client', custom_configs: dict = {}):
        super().__init__(host, port)
        
        # Create producer configs
        self.producer_configs = {'client.id': client_id,}
        self.producer_configs.update(self.client_configs)
        self.producer_configs.update(custom_configs)
        
        # Create producer
        self.producer = Producer(self.client_configs)

    def produce(self, topic, key=None, value=None):
        """Produce messages"""
        
        # Produce messages
        try:
            if key:
                self.producer.produce(topic=topic,
                                      key=key,
                                      value=value,
                                      callback=self.on_produce)
            else:
                self.producer.produce(topic=topic,
                                      value=value,
                                      callback=self.on_produce)
        except Exception as exc:
            self.handle_exception(exc)
        
    def on_produce(self, error, message):
        """Callback on produce"""
        
        # Treat callback on produce
        if error:
            print(f'failed message delivery: {error}')
        else:
            print(f'on_produce | '
                  f'produced message | '
                  f'topic: {message.topic()} | '
                  f'partition: {message.partition()} | '
                  f'offset: {message.offset()} | '
                  f'key: {message.key()} | '
                  f'value: {message.value()}')

    def poll(self, timeout: float = 1.0):
        """Poll messages"""
        
        # Poll messages (dispatch each message asynchronously)
        try:
            self.producer.poll(timeout)
        except Exception as exc:
            self.handle_exception(exc)

    def flush(self):
        """Flush messages"""
        
        # Flush messages (dispatch all messages synchronously)
        try:
            self.producer.flush()
        except Exception as exc:
            self.handle_exception(exc)

class KafkaConsumer(KafkaClient):
    """Kafka Consumer"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 9092,
                 group_id: str = 'nodi-group', custom_configs: dict = {},
                 access_list_size: int = 100000):
        super().__init__(host, port)
        
        # Create consumer configs
        self.consumer_configs = {'group.id': group_id,}
        self.consumer_configs.update(self.client_configs)
        self.consumer_configs.update(custom_configs)
        
        # Create consumer
        self.consumer = Consumer(self.consumer_configs)
        
        # Create admin for some functions
        self.admin = KafkaAdmin()
        
        # Create access list for external access
        self.access_list = deque(maxlen=access_list_size)
    
    def subscribe(self, topics: list[str]):
        """Subscribe topics"""
        
        # Subscribe topics
        self.consumer.subscribe(topics=topics,
                                on_assign=self.on_subscribe)
    
    def on_subscribe(self, consumer, partitions):
        """Callback on subscribe"""
        
        # Treat callback on subscribe
        print(f'on_subscribe | '
              f'consumer: {consumer} | '
              f'partitions: {partitions}')
    
    def unsubscribe(self):
        """Unsubscribe topics"""
        
        # Unsubscribe all topics
        self.consumer.unsubscribe()
    
    def assign(self, topic_partitions_info: list[tuple[str, int]]):
        """Assign topics to consumer""" 
        ...
        
        topic_partitions = []
        for topic, partition in topic_partitions_info:
            topic_partitions.append(TopicPartition(topic, partition))
        self.consumer.assign(topic_partitions)

    def consume(self, cycle: float = 0.001):
        """Consume messages"""
            
        # Create commit flag
        to_commit = False
        
        while True:
            
            try:
        
                # Poll messages
                message = self.consumer.poll(timeout=1.0)
                
                # If no messages, continue
                # If messages finished, commit
                if message is None:
                    if to_commit:
                        self.consumer.commit()
                        to_commit = False
                    continue
                
                # If error, handle exception
                if message.error():
                    if to_commit:
                        self.consumer.commit()
                        to_commit = False
                    self.handle_exception(message.error())
                
                # If messages and no error, treat message and store offsets
                else:
                    self.access_list.append(message)
                    self.on_message(message)
                    self.consumer.store_offsets(message)
                    to_commit = True
                        
            except Exception as exc:

                #self.consumer.close()
                self.handle_exception(exc)
            
            sleep(cycle)
    
    def on_message(self, message):
        """Callback on message"""
        
        # Treat callback on message
        print(f'on_message | '
              f'consumed message | '
              f'topic: {message.topic()} | '
              f'partition: {message.partition()} | '
              f'offset: {message.offset()} | '
              f'key: {message.key()} | '
              f'value: {message.value()}')
    
    def store_offsets(self):
        """Store offsets"""
        
        # Store offsets to broker
        try:
            self.consumer.store_offsets()
        except Exception as exc:
            self.handle_exception(exc)
    
    def commit(self):
        """Commit"""
        
        # Commit completion status to broker
        try:
            self.consumer.commit()
        except Exception as exc:
            self.handle_exception(exc)
        
    def close(self):
        """Close consumer"""
        
        # Close consumer and commit final offsets
        self.consumer.close()
        
    def get_watermark_offsets(self, topic: str, partition: int) -> tuple[int, int]:
        """Get latest offset and earliest offset of topic"""
            
        # Create topic partition to seek
        topic_partition = TopicPartition(topic, partition)

        # Get watermark offsets of topic
        low, high = self.consumer.get_watermark_offsets(topic_partition)
        return low, high
    
    def seek_to_offset(self, topic: str, partition: int, offset: int) -> None:
        """Force moving offset"""
        """input offset -1 to set the latest offset"""
        
        try:
            
            # Poll first to get assigned partition
            message = self.consumer.poll(timeout=1.0)
            
            # Create topic partition to seek
            topic_partition = TopicPartition(topic, partition, offset)
            
            # Seek to partition
            self.consumer.seek(topic_partition)
        
        except Exception as exc:
            self.handle_exception(exc)
    
    def get_assignments(self):
        """Get assigned topics to consumer"""
        topic_partitions = self.consumer.assignment()
        return topic_partitions
    
    def get_position(self, topic: str,
                     partition: int = None,
                     offset: int = None):
        """Get current offset position of target topic partition"""
        
        # Create topic partition to get
        if partition is None:
            topic_partition = TopicPartition(topic)
        elif offset is None:
            topic_partition = TopicPartition(topic, partition)
        else:
            topic_partition = TopicPartition(topic, partition, offset)
        
        # Get topic position
        topics = self.consumer.position([topic_partition])
        return topics
        
    def list_subscribed_topics(self):
        ...
        
        # try:
        #     # 소비자 그룹 목록 가져오기
        #     print(group_list)
        #     group_ids = [group[0] for group in group_list.groups]
        #     group_id = self.consumer_configs['group.id']
        #     if group_id not in group_ids:
        #         print(f"Consumer group {group_id} not found.")
        #         return

        #     # 특정 그룹의 상세 정보 가져오기
        #     group_descriptions = self.admin.describe_consumer_groups([group_id])

        #     for description in group_descriptions:
        #         if description.error():
        #             raise Exception(f"Error retrieving group info: {description.error()}")

        #         print(f"Consumer Group: {description.group}")
        #         print(f"State: {description.state}")
        #         print(f"Subscribed Topics:")

        #         # 멤버별로 할당된 토픽과 파티션을 출력
        #         for member in description.members:
        #             member_metadata = member.member_metadata
        #             # 멤버가 구독 중인 토픽 정보는 metadata에 포함됨
        #             topics = member_metadata.topics
        #             if topics:
        #                 for topic in topics:
        #                     print(f"  - Topic: {topic}")
        #             else:
        #                 print("  - No topics subscribed by this member.")

        # except Exception as e:
        #     print(f"Failed to retrieve consumer group information: {e}")

class KafkaAdmin(KafkaClient):
    """Kafka Admin"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 9092,
                 custom_configs: dict = {}):
        super().__init__(host, port)
        
        # Create admin configs
        self.admin_configs = {}
        self.admin_configs.update(self.client_configs)
        self.admin_configs.update(custom_configs)
        self.admin = AdminClient(self.admin_configs)
    
    def list_groups(self):
        """List all groups in cluster"""
        
        # Get groups list
        try:
            results = self.admin.list_groups()
            return results
        except Exception as exc:
            self.handle_exception(exc)
            return False
    
    def create_topics(self, topics: list[str], partition_number: int = 1,
                      replication_factor: int = 1):
        """Create topics"""
        
        results = []
        
        # Get new topic objects
        new_topics = []
        for topic in topics:
            topic_new = NewTopic(topic=topic,
                                 num_partitions=partition_number,
                                 replication_factor=replication_factor)
            new_topics.append(topic_new)
        
        # Create topics
        if new_topics:
            futures_dict = self.admin.create_topics(new_topics)
            
            # Check async results
            for topic, future in futures_dict.items():
                try:
                    future.result()
                    results.append(topic)
                except Exception as exc:
                    self.handle_exception(exc)
        
        # Return results
        return results
    
    def list_topics(self, topics: None | str = None):
        """List one topic or all topics in cluster"""
        
        # Get topics list
        try:
            results = self.admin.list_topics(topics).topics
            return results
        except Exception as exc:
            self.handle_exception(exc)
            return False

    def delete_topics(self, topics: list[str]):
        """Delete topics"""
        
        # Delete topics
        futures_dict = self.admin.delete_topics(topics)
        
        # Check async results
        results = []
        for topic, future in futures_dict.items():
            try:
                future.result()
                results.append(topic)
            except Exception as exc:
                self.handle_exception(exc)
        return results
    
    def reset_topics(self, topics: list[str],
                     partition_number: int = 1, replication_factor: int = 1,
                     check_interval: int = 1, timeout: int = 10) -> bool:
        """Reset topics"""
        
        # Create list to record topic creations
        deleted = []
        to_create = topics[:]
        created = []
        
        try:
            
            # Check start time
            time_start = time()
            
            # Delete all topics first
            deleted.extend(self.delete_topics(topics))
            if not deleted:
                return False
            
            # Then loop to create topics
            while True:
                
                # Create topics
                just_created = self.create_topics(topics=to_create,
                                                  partition_number=partition_number,
                                                  replication_factor=replication_factor)
                created.extend(just_created)
                to_create = list(set(to_create) - set(just_created))
                
                # If all topics created, break loop
                if not to_create:
                    break
                
                # If timeout, raise timeout error
                time_elapsed = time() - time_start
                if time_elapsed >= timeout:
                    raise TimeoutError
                    
                # Wait for next check
                sleep(check_interval)

        except Exception as exc:
            self.handle_exception(exc)

        # Create topics
        return {'deleted': deleted, 'created': created}
        
    def describe_topics(self, topics: list[str]) -> dict:
        """Describe topics detail"""
        
        try:

            # Create topics desc dict
            topics_desc = {}
            
            # Get topics metadata
            topics_metadata_dict = self.list_topics()
            
            # Iterate topics
            for topic in topics:
                
                # If topic not exists, continue
                if topic not in topics_metadata_dict:
                    topics_desc[topic] = {'error': 'topic does not exist'}
                    continue
                
                # Structure topic details
                topic_metadata = topics_metadata_dict[topic]
                topic_info = {
                    'partitions': len(topic_metadata.partitions),
                    'partitions_info': {},
                    'error': topic_metadata.error,
                }

                # Get replication factor from the first partition's replicas
                if topic_metadata.partitions:
                    partition_replication_factor = len(next(iter(topic_metadata.partitions.values())).replicas)
                    topic_info["replication_factor"] = partition_replication_factor

                # Loop through partitions for the topic
                for partition, partition_metadata in topic_metadata.partitions.items():
                    partition_info = {
                        "leader": partition_metadata.leader,
                        "replicas": partition_metadata.replicas,
                        "isrs": partition_metadata.isrs,
                        "error": partition_metadata.error
                    }
                    topic_info["partitions_info"][partition] = partition_info

                topics_desc[topic] = topic_info

            return topics_desc

        except Exception as exc:
            self.handle_exception(exc)
            return {"error": str(exc)}

    def get_topics_config(self, topics: list[str]):
        """Get config from topics"""
        try:
            resources = []
            for topic in topics:
                resource = ConfigResource('topic', topic)
                resources.append(resource)
            futures = self.admin.describe_configs(resources)
            results = {}
            for resource, future in futures.items():
                topic = resource.name
                results[topic] = {}
                configs = future.result()
                for config, entry in configs.items():
                    results[topic][config] = entry.value
            return results
        except Exception as exc:
            self.handle_exception(exc)
            return False

    def list_groups(self):
        """List all consumer groups in the cluster"""
        
        try:
            # Get groups list
            groups_future = self.admin.list_consumer_groups()
            groups_result = groups_future.result()
            
            # Get valid groups
            valid_groups = groups_result.valid
            
            # Parse groups object
            results = []
            for group in valid_groups:
                group_info = {
                    group.group_id: {
                        'simple_group': group.is_simple_consumer_group,
                        'state': group.state,}}
                results.append(group_info)
            return results
        
        except Exception as exc:
            self.handle_exception(exc)
            return False
        
    def delete_groups(self, groups: list[str]):
        """Delete consumer groups"""
        
        # Delete consumer groups
        futures_dict = self.admin.delete_consumer_groups(groups)
        
        # Check async results
        results = []
        for group, future in futures_dict.items():
            try:
                future.result()
                results.append(group)
            except Exception as exc:
                self.handle_error(exc)
        
        # Return successfully deleted groups
        return results
    
    def reset_groups(self, group_id: str, reset_only: bool = False):
        """Delete or reset the given consumer group."""
        try:
            if reset_only:
                # Just reset offsets to 0 for all topics of the group
                offsets = self.consumer.committed(self.consumer.assignment())
                for offset in offsets:
                    offset.offset = 0
                self.consumer.commit(offsets=offsets)
                print(f'Offsets for group {group_id} have been reset.')
            else:
                # Deleting the consumer group (Kafka doesn't provide direct deletion API)
                # So, we can reset it by assigning 0 offsets and consuming till the end.
                print(f'Attempting to delete group {group_id} by resetting its offsets...')
                self.reset_offsets_to_zero(group_id, topics=[t.topic for t in self.consumer.assignment()])
            return True
        except Exception as exc:
            self.handle_error(exc)
            return False
            
    # def alter_topics_config(self, topic_configs: dict):
    #     """Alter config for topics"""
    #     ...

    # def increase_partitions(self, topic: str, partition_number: int):
    #     """Increase the number of partitions for a topic"""
    #     partition_new = {topic: NewPartitions(topic=topic,
    #                                           new_total_count=partition_number)}
    #     futures = self.admin.create_partitions(partition_new)
    #     for topic, future in futures.items():
    #         try:
    #             future.result()
    #             return True
    #         except Exception as exc:
    #             self.handle_error(KafkaException(f'failed increase partition on {topic}: {exc}'))
    #             return False
    
    # def list_consumer_groups(self):  #TODO
    #     """List all consumer groups in cluster"""
    #     try:
    #         consumer_groups = self.admin.list_consumer_groups()
    #         valid_groups = consumer_groups.result().valid
    #         error_groups = consumer_groups.result().errors
    #         results = {'valid': [],
    #                    'error': [],}
    #         for group in valid_groups:
    #             result = {'group_id': group[0],
    #                       'state': group[1].state,
    #                       'is_simple_consumer_group': group[1].is_simple_consumer_group,}
    #             results['valid'].append(result)            
    #         for error in error_groups:
    #             result = {'group_id': error[0],
    #                       'error': str(error[1]),}
    #             results['error'].append(result)
    #         return results
    #     except Exception as exc:
    #         self.handle_exception(exc)
    #         return None




    
if __name__ == '__main__':
    import sys
    sys.path.append('/root/edge')
    from time import sleep, time
    from threading import Thread
    from pkg.time_tool import get_current_timestamp
    from pickle import dumps, loads
    
    custom_configs = {'enable.auto.offset.store': False,
                      'session.timeout.ms': 6000,
                      'auto.offset.reset': 'latest',
                      'heartbeat.interval.ms': 1000,}
    
    if sys.argv[1] == 'p':
        p = KafkaProducer()

        # mask produce callback
        def on_produce(error, message): ...
        p.on_produce = on_produce

        d = {}
        t = get_current_timestamp()
        for i in range(10000):
            k = f'tag-0{str(i).zfill(4)}'
            d[k] = {'v': i, 'gt': t, 'gq': 'good', 'st': t, 'sq': 'good'}
        print(len(d))
        check = time()
        pkl = dumps(d)
        print(time() - check)
        # for i in range(10000):
        #     p.produce(topic='test-topic1', key='test-key', value=f'Hello Kafka {i}')
        check = time()
        for i in range(100):
            p.produce(topic='test-topic1', key=None, value=pkl)
        print(time() - check)
        p.flush()
        
    if sys.argv[1] == 'c':
        c = KafkaConsumer(group_id='test-group3', custom_configs=custom_configs)
        c.admin.create_topics(['test-topic', 'test-topic1', 'test-topic2'])
        c.subscribe(['test-topic', 'test-topic1', 'test-topic2'])
        lo, hi = c.get_watermark_offsets('test-topic1', 0)
        c.seek_to_offset('test-topic1', 0, hi-10)

        # mask message callback
        def on_message(message): ...
        c.on_message = on_message
        
        # topics = []
        # for i in range(3000):
        #     topics.append(f'kac.0{str(i + 1).zfill(4)}')
        # c.subscribe(topics)
        # for i in topics:
        #     try:
        #         lo, hi = c.get_watermark_offsets(i, 0)
        #         c.seek_to_offset(i, 0, hi)
        #     except:
        #         pass
        t = Thread(target=c.consume, daemon=True)
        t.start()

        while True:
            cnt = 0
            while c.access_list:
                message = c.access_list.popleft()
                cnt += 1
            print(cnt)
            sleep(1)

    if sys.argv[1] == 'a':
        a = KafkaAdmin(host='0.0.0.0', port=9092)
        c = KafkaConsumer(group_id='test-group', custom_configs=custom_configs)
        c.subscribe(['test-topic1'])
        # print('---')
        # print(c.set_offsets_to_zero(['test-topic']))
        # print('---')
        # print(c.set_offsets_to_latest(['test-topic']))
        # print('---')
        # print(a.delete_topics(['test-topic']))
        # print('---')
        # print(a.create_topics(['test-topic']))
        # print('---')
        topics = a.list_topics()
        for topic in topics:
            print(topic)
        # print('---')
        # print(a.reset_topics(['test-topic', 'test-topic1', 'test-topic2', 'test-topic3', 'test-topic4']))
        # print('---')
        # print(a.list_topics())
        # print('---')
        # print(a.describe_topics(['test-topic', 'test-topic1', 'test-topic4']))
        # print('---')
        # print(a.list_groups())
        # print('---')
        # print(c.assign([('test-topic1', 0)]))
        # print('---')
        # print(a.list_groups())
        # print('---')
        # print(c.get_watermark_offsets('test-topic1', 0))
        # print('---')
        # print(c.seek_to_offset('test-topic1', 0, 9990))
        # c.consume()





