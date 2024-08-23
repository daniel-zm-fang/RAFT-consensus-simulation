import random
import threading
import time
import logging
from enum import Enum


class NodeRole(Enum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


class Node:
    def __init__(self, node_id, cluster):
        self.id = node_id
        self.cluster = cluster
        self.role = NodeRole.FOLLOWER
        self.term = 0
        self.log = []
        self.voted_for = None
        self.votes_received = 0
        self.election_timeout = random.uniform(500, 800) / 1000
        self.last_heartbeat = time.time()
        self.logger = logging.getLogger(f"Node-{self.id}")
        self.running = True
        self.lock = threading.Lock()

    def run(self):
        while self.running:
            with self.lock:
                if self.role == NodeRole.FOLLOWER:
                    self.run_follower()
                elif self.role == NodeRole.CANDIDATE:
                    self.run_candidate()
                elif self.role == NodeRole.LEADER:
                    self.run_leader()
            time.sleep(0.01)  # Small sleep to prevent busy waiting

    def stop(self):
        with self.lock:
            self.running = False

    def run_follower(self):
        if time.time() - self.last_heartbeat > self.election_timeout:
            self.start_election()

    def run_candidate(self):
        if self.votes_received > len(self.cluster.nodes) // 2:
            self.become_leader()
        elif time.time() - self.last_heartbeat > self.election_timeout:
            self.start_election()

    def run_leader(self):
        self.send_heartbeats()

    def start_election(self):
        self.role = NodeRole.CANDIDATE
        self.term += 1
        self.voted_for = self.id
        self.votes_received = 1
        self.last_heartbeat = time.time()
        self.logger.info(f"Node-{self.id} starting election for term {self.term}")
        self.request_votes()

    def request_votes(self):
        for node in self.cluster.nodes:
            if node.id != self.id:
                self.cluster.send_message(
                    self.id,
                    node.id,
                    {"type": "RequestVote", "term": self.term, "candidate_id": self.id},
                )

    def handle_vote_request(self, sender_id, message):
        with self.lock:
            if message["term"] > self.term:
                self.term = message["term"]
                self.role = NodeRole.FOLLOWER
                self.voted_for = None

            if message["term"] == self.term and (
                self.voted_for is None or self.voted_for == message["candidate_id"]
            ):
                self.voted_for = message["candidate_id"]
                self.last_heartbeat = time.time()
                self.logger.info(
                    f"Node-{self.id} granting vote to Node-{sender_id} for term {self.term}"
                )
                return {"type": "VoteResponse", "term": self.term, "vote_granted": True}

            return {"type": "VoteResponse", "term": self.term, "vote_granted": False}

    def handle_vote_response(self, sender_id, message):
        with self.lock:
            if message["term"] > self.term:
                self.term = message["term"]
                self.role = NodeRole.FOLLOWER
                self.voted_for = None
            elif self.role == NodeRole.CANDIDATE and message["vote_granted"]:
                self.votes_received += 1
                self.logger.info(
                    f"Node-{self.id} received vote from Node-{sender_id}, total votes: {self.votes_received}"
                )

    def become_leader(self):
        self.role = NodeRole.LEADER
        self.logger.info(f"Node-{self.id} became leader for term {self.term}")
        self.send_heartbeats()

    def send_heartbeats(self):
        for node in self.cluster.nodes:
            if node.id != self.id:
                self.cluster.send_message(
                    self.id,
                    node.id,
                    {"type": "AppendEntries", "term": self.term, "leader_id": self.id},
                )

    def handle_append_entries(self, sender_id, message):
        with self.lock:
            if message["term"] >= self.term:
                if self.role != NodeRole.FOLLOWER or message["term"] > self.term:
                    self.logger.info(
                        f"Node-{self.id} updated to follower state, term: {message['term']}"
                    )
                self.term = message["term"]
                self.role = NodeRole.FOLLOWER
                self.voted_for = None
                self.last_heartbeat = time.time()


class Cluster:
    def __init__(self, node_count):
        self.nodes = [Node(i, self) for i in range(node_count)]
        self.logger = logging.getLogger("Cluster")
        self.message_queue = []
        self.queue_lock = threading.Lock()

    def send_message(self, sender_id, target_id, message):
        with self.queue_lock:
            self.message_queue.append((sender_id, target_id, message))

    def process_messages(self):
        with self.queue_lock:
            for sender_id, target_id, message in self.message_queue:
                target_node = self.nodes[target_id]
                if message["type"] == "RequestVote":
                    response = target_node.handle_vote_request(sender_id, message)
                    self.nodes[sender_id].handle_vote_response(target_id, response)
                elif message["type"] == "AppendEntries":
                    target_node.handle_append_entries(sender_id, message)
            self.message_queue.clear()

    def run_simulation(self, duration=10):
        threads = [threading.Thread(target=node.run) for node in self.nodes]
        for thread in threads:
            thread.start()

        start_time = time.time()
        while time.time() - start_time < duration:
            self.process_messages()
            self.print_status()
            time.sleep(1)

        # Stop all nodes
        for node in self.nodes:
            node.stop()

        # Process any remaining messages
        self.process_messages()

        # Wait for all threads to finish
        for thread in threads:
            thread.join(timeout=0.1)

        self.logger.info("Simulation completed.")

    def print_status(self):
        status = [
            f"Node-{node.id}: Role={node.role.value}, Term={node.term}"
            for node in self.nodes
        ]
        self.logger.info("Cluster Status: " + " | ".join(status))


if __name__ == "__main__":
    random.seed(42)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    cluster = Cluster(node_count=5)
    cluster.run_simulation(duration=10)
