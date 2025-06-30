def get_between(es,index,start,end,userid):
    return es.search(index=index, query={
        "bool": {
            "must": [
                {
                    "match": {
                        "userid": userid
                    }
                },
                {
                    "range": {
                        "date": {
                           "gte": start,  
                            "lte":end
                        }
                    }
                }
            ]
        }
    })["hits"]["hits"]