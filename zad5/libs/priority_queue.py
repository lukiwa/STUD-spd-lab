from typing import Iterable, Tuple
import operator

class PriorityQueue():
  
    def __init__(self, compare=operator.lt):
        self.heap = []
        self.compare = compare

    def len(self):
        return len(self.heap)

    def __heapify_up(self, child_index):
        heap, compare = self.heap, self.compare
        child = child_index
        #while child not at root
        while child > 0:

            # Move the index to the parent
            parent = child // 2
            
            # Check if the element is less/greater (depending on comaprator)
            # than its parent swap the elements - if false - swap elements
            if compare(heap[parent], heap[child]):
                return

            heap[parent], heap[child] = heap[child], heap[parent]
            child = parent

    def __heapify_down(self, parent_index):
        heap, compare = self.heap, self.compare
        length = len(heap)

        #if heap contains one element
        if length == 1:
            return
        parent = parent_index

        # if the current node has at least one child
        while 2 * parent < length:
            child = 2 * parent
            # Get the index of the min/max value child of the current node
            if child + 1 < length and compare(heap[child + 1], heap[child]):
                child += 1
            if compare(heap[parent], heap[child]):
                return

            # Swap the values of the current element is greater/lesser than its min/max child
            heap[parent], heap[child] = heap[child], heap[parent]
            parent = child

    def pop(self):
        heap = self.heap
        
        #get last element and check if heap will not be empty
        last_element = heap.pop()
        if len(heap) == 0:
            return last_element

        #min/max element is always the root
        item = heap[0]

        #last element is now root
        heap[0] = last_element

        #move it down the tree
        self.__heapify_down(0)
        return item

    def peek(self):
        if len(self.heap) == 0:
            return None
        return self.heap[0]

    def push(self, element):
        self.heap.append(element)
        self.__heapify_up(len(self.heap) - 1)