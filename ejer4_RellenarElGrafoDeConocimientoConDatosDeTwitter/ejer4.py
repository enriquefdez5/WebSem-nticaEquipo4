import json
import textacy
import spacy
from simhash import Simhash, SimhashIndex
from rdflib import Graph, BNode, Literal
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore, _node_to_sparql
from rdflib.namespace import RDF, XSD, Namespace

# Se obtienen las líneas de la colección
lineas = open("./tweets-tornadoes-high_accuracy-expanded.ndjson", encoding="utf8").readlines()

# Lectura de tweets de la colección
tuits = []
for linea in lineas:
    tuit = json.loads(linea)
    tuits.append(tuit)

# Búsqueda de duplicados mediante simhash
firmas_tuits = []
valor_f = 128
observaciones = []

for i in range(len(tuits)):
    tuit = tuits[i]
    firma = Simhash(tuit["full_text"], f=valor_f)
    firmas_tuits.append((i, firma))

indice = SimhashIndex(firmas_tuits, k=10, f=valor_f)

# Nos quedamos con los tweets únicos y sus índices
tuits_unicos = []
index_list = []
for i in range(len(tuits)):
    tuit = tuits[i]

    firma = Simhash(tuit["full_text"], f=valor_f)
    duplicados = indice.get_near_dups(firma)

    if len(duplicados) == 1:
        tuits_unicos.append(tuit)
        index_list.append(i)

# Filtramos los verificados
verifieds = []

for i in range(len(lineas)):
    if i in index_list:
        if json.loads(lineas[i])["user"]["verified"]:
            verifieds.append(lineas[i])


# Connect to fuseki triplestore
# Función para convertir blank nodes. Si no existe peta porque no sabe procesar la clase BNode
def my_bnode_ext(node):
    if isinstance(node, BNode):
        return '<bnode:b%s>' % node
    return _node_to_sparql(node)


# Parseamos la fecha del tweet al formato dateTime de XSD
def get_created_at(created_at_value):
    print(created_at_value)
    split = created_at_value.split(" ")
    year = split[5]
    # son todos de mayo
    month = "05"
    day = split[2]
    hour = split[3]
    return "{0}-{1}-{2}T{3}".format(year, month, day, hour)


# Creo la store con los endpoitns
store = SPARQLUpdateStore('http://156.35.98.103:3030/tornados/update', node_to_sparql=my_bnode_ext)
query_endpoint = "http://156.35.98.103:3030/tornados/query"
update_endpoint = "http://156.35.98.103:3030/tornados/update"
store.open((query_endpoint, update_endpoint))

graph = Graph(store)

# define example namespace
prefix_ex = Namespace("http://example.org/")
prefix_om = Namespace("http://opendata.caceres.es/def/ontomunicipio#")
prefix_out = Namespace("http://ontologies.hypios.com/out#")
prefix_ou = Namespace("http://opendata.unex.es/def/ontouniversidad#")
prefix_sx = Namespace("http://shex.io/ns/shex#")
prefix_sd = Namespace("http://www.w3.org/ns/sparql-service-description#")
prefix_st = Namespace("http://sweetontology.net/phenAtmoPrecipitation/")
prefix_stf = Namespace("http://sweetontology.net/stateStorm/")
prefix_location = Namespace("http://sw.deri.org/2006/07/location/loc#")
prefix_loc = Namespace("http://www.w3.org/2007/uwa/context/location.owl#")
prefix_schema = Namespace("http://schema.org/")
prefix_sc = Namespace("http://purl.org/science/owl/sciencecommons/")
prefix_fo = Namespace("http://purl.org/ontology/fo/")
prefix_db = Namespace("http://dbpedia.org/resource/classes#")
prefix_oum = Namespace("http://www.ontology-of-units-of-measure.org/resource/om-2/")

tornado_idx = 10000

# Creamos primeros nodos del grafo
graph.add((prefix_ex.tornados, RDF.first, prefix_ex.tornado + str(tornado_idx)))
graph.add((prefix_ex.tornados, RDF.rest, prefix_ex.listItem + str(tornado_idx)))

nlp = spacy.load("en_core_web_lg")
# Por cada tuit se creará un tornado... Tarda bastante, son 3300 nodos aprox.
for tuit in verifieds:
    json_tuit = json.loads(tuit)
    # Si tiene coordenadas
    if json_tuit["coordinates"] != None:
        coordinates = json_tuit["coordinates"]["coordinates"]
        longitude = coordinates[0]
        latitude = coordinates[1]
    # Si tiene place
    elif json_tuit["place"] != None:
        state_value = json_tuit["place"]["full_name"]
        county = json_tuit["place"]["name"]
    # Fecha de creación y fuente
    created_at = get_created_at(json_tuit["created_at"])
    source = json_tuit["user"]["name"]
    # Probamos a buscar información en KWIC y NER, pero no hay mucha info y no es muy útil. Aunque sean fechas cercanas
    # y la mayoría de sitios mencionados son cercanos no fuimos capaces de justificar que fueran el mismo tornado al
    # no haber aplicado ningún algoritmo de clustering
    doc = nlp(json_tuit["full_text"])
    kwic_etiqueta_a_buscar = "injuries"
    entities = textacy.extract.kwic.keyword_in_context(doc, kwic_etiqueta_a_buscar, window_width=50)
    for entity in entities:
        print(entity)
    etiqueta_a_buscar = "deaths"
    for entidad in doc.ents:
        etiqueta = entidad.label_
        texto = entidad.text
        if etiqueta_a_buscar in texto:
            print(texto)

    # Se crean los nodos
    node0 = (prefix_ex.listItem + str(tornado_idx), RDF.first, prefix_ex.tornado + str(tornado_idx))
    node1 = (prefix_ex.tornado + str(tornado_idx), RDF.type, prefix_st.Tornado)
    init_datetime_literal = Literal(created_at, datatype=XSD.dateTime)
    node2 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.initDateTime, init_datetime_literal)

    state = (prefix_ex.tornado_state + str(tornado_idx), RDF.type, prefix_schema.State)
    if not 'state_value' in locals():
        state_value = "notDefined"
        county = "notDefined"
    state_address = Literal(state_value, datatype=prefix_schema.address)
    state_county = Literal(county, datatype=XSD.string)
    state2 = (prefix_ex.tornado_state + str(tornado_idx), prefix_schema.address, state_address)
    state3 = (prefix_ex.tornado_state + str(tornado_idx), prefix_ex.county, state_county)

    node3 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.state, prefix_ex.tornado_state + str(tornado_idx))

    report_source = (prefix_ex.reportSource + str(tornado_idx), RDF.type, prefix_schema.Report)
    report_number_literal = Literal(source, datatype=prefix_schema.reportNumber)
    report_source2 = (prefix_ex.reportSource + str(tornado_idx), prefix_schema.reportNumber, report_number_literal)

    node4 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.reportSource, prefix_ex.report_source + str(tornado_idx))

    if not 'longitude' in locals():
        longitude = 0
        begin_lon = 0
    init_coordinates = (prefix_ex.init_coordinates + str(tornado_idx), RDF.type, prefix_schema.GeoCoordinates)
    begin_latitude_literal = Literal(latitude, datatype=prefix_schema.latitude)
    begin_longitude_literal = Literal(longitude, datatype=prefix_schema.longitude)
    init_coordinates2 = (prefix_ex.init_coodinates + str(tornado_idx), prefix_ex.latitude, begin_latitude_literal)
    init_coordinates3 = (prefix_ex.init_coodinates + str(tornado_idx), prefix_ex.longitude, begin_longitude_literal)
    node5 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.init, prefix_ex.init_coordinates + str(tornado_idx))

    # Se añaden los nodos
    graph.add(node0)
    graph.add(node1)
    graph.add(node2)
    graph.add(state)
    graph.add(state2)
    graph.add(state3)
    graph.add(node3)
    graph.add(report_source)
    graph.add(report_source2)
    graph.add(node4)
    graph.add(init_coordinates)
    graph.add(init_coordinates2)
    graph.add(init_coordinates3)
    graph.add(node5)
    if tornado_idx < len(verifieds) + 10000:
        graph.add((prefix_ex.listItem + str(tornado_idx), RDF.rest, prefix_ex.listItem + str(tornado_idx + 1)))
    else:
        graph.add((prefix_ex.listItem + str(tornado_idx), RDF.rest, RDF.nil))
    tornado_idx = tornado_idx + 1
