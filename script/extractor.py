import os
from bs4 import BeautifulSoup
import jsonlines as jl


class JavaClass:
    def __init__(self, directory, fqn):
        self.directory = directory
        self.fqn = fqn

    def __str__(self):
        return self.directory + ' ' + self.fqn


class Extractor:
    @staticmethod
    def extract(doc_path):
        class_list = []
        class_offset = len(doc_path.rstrip('/').split('/')) - 1

        for dir, sub_dir, files in os.walk(doc_path):
            if not files:
                continue
            package = dir.split('/')
            if package[-1] == 'class-use' or package[-1] == 'doc-files':
                continue
            package = package[class_offset:]
            package = '.'.join(package)

            for f in files:
                if f[0] < 'A' or f[0] > 'Z':
                    continue
                name = f[:-5]

                clazz = JavaClass(dir + '/' + f, package + '.' + name)
                class_list.append(clazz)

        return class_list

    @staticmethod
    def parse_html(file, fqn=None):
        method_map = {}
        soup = BeautifulSoup(open(file), 'lxml')

        # find summary
        tr = soup.find(name='tr', attrs={'id':'i0'})
        if tr is None:
            return []
        method_name_tag = tr.td.find_next_sibling()
        method_name = method_name_tag.code.span.a.text
        method_summary_tag = method_name_tag.div
        if method_summary_tag is None:  # summary not exists
            method_summary = ''
        else:
            method_summary = method_summary_tag.text
        method = {'summary': method_summary}
        method_map[method_name] = method

        for sibling in tr.find_next_siblings("tr"):
            method_name_tag = sibling.td.find_next_sibling()
            method_name = method_name_tag.code.span.a.text
            method_summary_tag = method_name_tag.div
            if method_summary_tag is None:  # summary not exists
                method_summary = ''
            else:
                method_summary = method_summary_tag.text
            method = {'summary': method_summary}
            method_map[method_name] = method

        # find remarks
        a = soup.find(name="a", attrs={"name": "method.detail"})
        for sibling in a.find_next_siblings("ul"):
            method_name_tag = sibling.li.h4
            method_name = method_name_tag.text
            descriptions = method_name_tag.find_next_siblings(name='div', attrs={'class': 'block'})
            description_list = []
            for description in descriptions:
                if description.text.startswith('Description copied from'):
                    continue
                description_list.append(description.text)
            method_map[method_name]['remarks'] = description_list

        method_list = []
        for method_name, method in method_map.items():
            method_list.append({'fqn': fqn + '.' + method_name,
                                'summary': method['summary'],
                                'remarks': method['remarks']})
        return method_list

    @staticmethod
    def get_method_list(clazz):
        try:
            method_list = Extractor.parse_html(clazz.directory, clazz.fqn)
            return method_list
        except Exception as e:
            print(clazz.fqn)
            print(e)
            return []


if __name__ == '__main__':
    DEBUG = False
    if not DEBUG:
        doc_path = '../../docs/api/java/'
        class_list = Extractor.extract(doc_path)

        method_list = []
        for clazz in class_list:
            method_list.extend(Extractor.get_method_list(clazz))

        if not os.path.exists('../out'):
            os.mkdir('../out')
        with jl.open('../out/method.jsonl', mode='w') as writer:
            for method in method_list:
                writer.write(method)
    else:
        res = Extractor.parse_html('../../docs/api/java/awt/MenuContainer.html', 'java.net.MulticastSocket')
        print(res)
