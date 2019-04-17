
query = '''{

root(id: 3, info: "info") {
  sub1 {
    sub2(some: 0, arg: 1) {
      a b c
    }
    the
    rest
    of
    it
  }
}

}'''

info = '''
{"this": 0, "is": 1, "info": "2"}
'''