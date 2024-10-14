import random

class TrieNode:
    def __init__(self):
        self.children = {}  # 字符到子节点的映射
        self.values = []    # 当前节点的所有值

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, words, value):
        words = '-'.join(words)
        node = self.root
        for char in words:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.values.append(value)  # 插入值到末尾节点

    def search_by_keys(self, prefix_words):
        node = self.root
        results = []
        prefix = '-'.join(prefix_words)

        # 1. 先找匹配前缀的节点
        for char in prefix:
            if char not in node.children:
                return results  # 找不到匹配的前缀
            node = node.children[char]

        # 2. 从前缀节点开始，收集所有子节点的值
        def collect_values(n):
            results.extend(n.values)  # 加入当前节点的值
            for child in n.children.values():
                collect_values(child)  # 递归收集子节点的值

        collect_values(node)  # 开始从匹配的前缀节点递归收集
        return results

    def get_by_keys(self, words):
        match_values = self.search_by_keys(words)
        return random.choice(match_values)


gender_dict = {
    'male': 'male',
    'female': 'female'
}
age_dict = {
    'child': 'child',
    'junior': 'junior',
    'senior': 'senior'
}
bg_dict = {
    'urban': 'urban',
    'scenery': 'scenery',
    'pure': 'pure'
}

trie_human = Trie()
trie_human.insert(
    [gender_dict['female'], age_dict['junior'], bg_dict['urban']],
    'https://clothing-try-on-1306401232.cos.ap-guangzhou.myqcloud.com/presave_persons/female-young-street-1.jpg'
)
trie_human.insert(
    [gender_dict['female'], age_dict['junior'], bg_dict['scenery']],
    'https://clothing-try-on-1306401232.cos.ap-guangzhou.myqcloud.com/presave_persons/female-young-scenary-1.png'
)
trie_human.insert(
    [gender_dict['female'], age_dict['junior'], bg_dict['pure']],
    'https://clothing-try-on-1306401232.cos.ap-guangzhou.myqcloud.com/presave_persons/female-yound-pure-1.jpg'
)


if __name__ == '__main__':
  # 示例使用
  # 输入 'ha'，应该返回 [1, 2]
  print(trie_human.search_by_keys(['female', 'junior', 'pure']))  # 输出1个

  # 输入 'hat'，应该返回 [1]
  print(trie_human.search_by_keys(['female', 'junior']))  # 输出3个
  print(trie_human.get_by_keys(['female', 'junior']))  # 输出1个

  # 输入 'h', 应该返回 [1, 2]
  print(trie_human.search_by_keys(['female', 'old']))  # 输出0个
