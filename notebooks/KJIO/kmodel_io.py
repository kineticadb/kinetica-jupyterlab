import gpudb
import os
import collections

KDBC = gpudb.GPUdb(encoding='BINARY', host='127.0.0.1', port='9191')

class KModelIO(object):
    def __init__(self,h_db=KDBC):
        self.h_db=h_db
        self.file_type = """
                    {
                            "type": "record",
                            "name": "file_type",
                            "fields": [
                                    {"name":"model_binary","type":"bytes"},
                                    {"name":"model","type":"string"},
                                    {"name":"model_id","type":"string"},
                                    {"name":"Accuracy","type":"double"},
                                    {"name":"Data_Time_created","type":"string"}
                            ]
                    }""".replace('\n', '').replace(' ', '')
        self.type_properties = {"model_id": ["char64"], "Data_Time_created": ["datetime"]}
        
        
    def Model2Kinetica(self,pbfile=None,sess=None,graph=None,output_node_names=None,ModelName="Model",Loss=0.99, COLLECTION="Network"):
        """
        pbfile can be a path to a local file or a pickle bytes.
        """
        import uuid
        from time import gmtime, strftime
        datetime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        from tensorflow import graph_util
        h_db = self.h_db

        # create model table if not exist
        table = 'TFmodel'
        type_def=self.file_type
        if not h_db.has_table(table_name=table)['table_exists']:
            response = h_db.create_type(type_definition=type_def,
                                        label=table, properties=self.type_properties)
            h_db.create_table(table_name=table, type_id=response['type_id'],
                                         options={"collection_name": COLLECTION})

        # generate output binary string
        # output_node_names example,output_node_names = "input,output,output2"
        #print "works 1"
        if pbfile !=None:
            if len(pbfile)<256:
                model=open(pbfile,'rb').read()
            else:
                model=pbfile
            #print "works 2"
        else:
            output_graph_def = graph_util.convert_variables_to_constants(
                sess,  # The session is used to retrieve the weights
                graph.as_graph_def(),
                output_node_names.split(",")  # The output node names are used to select the usefull nodes
            )
            model=output_graph_def.SerializeToString()
        # insert model into kinetica
        encoded_obj_list = []
        ID = str(uuid.uuid1())
        datum = collections.OrderedDict()
        datum["model_binary"] = model
        datum["model"] = ModelName
        datum["model_id"] = ID
        datum["Accuracy"] = Loss
        datum["Data_Time_created"] = datetime
        encoded_obj_list.append(h_db.encode_datum(self.file_type, datum))
        options = {'update_on_existing_pk': 'true'}
        response = h_db.insert_records(table_name=table, data=encoded_obj_list, list_encoding='binary', options=options)
        return ID
        

    def Model_from_Kinetica(self,Model_ID):
        from tensorflow import GraphDef,Graph,import_graph_def
        h_db = self.h_db
        response = h_db.get_records(table_name='TFmodel', encoding="binary",
                                    options={'expression': "model_id=\"" + Model_ID + "\""})
        records = gpudb.GPUdbRecord.decode_binary_data(response["type_schema"], response["records_binary"])
        record=records[0]
        record["model_binary"]
        graph_def = GraphDef()
        graph_def.ParseFromString(record["model_binary"])

        graph = Graph()
        with graph.as_default():
            # The name var will prefix every op/nodes in your graph
            # Since we load everything in a new graph, this is not needed
            import_graph_def(graph_def)
        return graph
    
    
    def SkModel_from_Kinetica(self,Model_ID):
        #from tensorflow import GraphDef,Graph,import_graph_def
        response = self.h_db.get_records(table_name='TFmodel', encoding="binary",
                                    options={'expression': "model_id=\"" + Model_ID + "\""})
        records = gpudb.GPUdbRecord.decode_binary_data(response["type_schema"], response["records_binary"])
        return records[0]["model_binary"]
    

    def getData(self, table='Mnist_train', offset=0, numberData=1):
        h_db=self.h_db
        response = h_db.get_records(table_name=table, offset=offset, limit=numberData)
        res_decoded = gpudb.GPUdbRecord.decode_binary_data(response["type_schema"], response["records_binary"])
        return res_decoded
