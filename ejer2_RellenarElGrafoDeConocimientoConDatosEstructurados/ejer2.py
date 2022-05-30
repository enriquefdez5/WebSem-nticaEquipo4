from bs4 import BeautifulSoup
from rdflib import Graph, BNode, Literal
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore, _node_to_sparql
from rdflib.namespace import RDF, XSD, Namespace
import requests

# Se hace la petición a una consulta de la web de NOAA.
base_url = "https://www.ncdc.noaa.gov/stormevents/"
r = requests.get(
    "{0}/listevents.jsp?eventType=ALL&beginDate_mm=02&beginDate_dd=01&beginDate_yyyy=2021&endDate_mm=02&endDate_dd=28&endDate_yyyy=2022&county=ALL&hailfilter=0.00&tornfilter=0&windfilter=000&sort=DT&submitbutton=Search&statefips=17%2CILLINOIS".format(
        base_url))
# Se parsea el resultado de la request con lxml
soup = BeautifulSoup(r.text, 'lxml')
# Se buscan todos los enlaces de la consulta, para buscar los tornados.
tornado_links = soup.find_all('a')

# Limitamos a 30 tornados para que no sea infinito
number_of_tornados = 30
current_tornado = 0
link_list = []
for tornado_link in tornado_links:
    if current_tornado < number_of_tornados:
        tornado_link_href = tornado_link.get("href")
        if "eventdetails" in tornado_link_href:
            link_list.append(tornado_link_href)

tornados = {}


# Connect to fuseki triplestore
# Función para convertir blank nodes. Si no existe peta porque no sabe procesar la clase BNode
def my_bnode_ext(node):
    if isinstance(node, BNode):
        return '<bnode:b%s>' % node
    return _node_to_sparql(node)


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

# El idx para definir los nombres de los tornados y el max para limitar cuantos añadimos y que no se haga eterno
tornado_idx = 0
tornado_max = 30

# Añadimos la primera parte de la lista de tornados
graph.add((prefix_ex.tornados, RDF.first, prefix_ex.tornado + str(tornado_idx)))
graph.add((prefix_ex.tornados, RDF.rest, prefix_ex.listItem + str(tornado_idx)))
# Para cada enlace de tornados, procesamos infor y creamos nodos
for link in link_list:
    if tornado_idx < tornado_max:
        # [:-1] porque el último caracter es un espacio en blanco que hace que la URL sea incorrecta y devuelva un error
        # 400 la petición
        url = "{0}{1}".format(base_url, link)[:-1]
        tornados_result = requests.get(url)
        tornado_soup = BeautifulSoup(tornados_result.text, 'lxml')
        # procesamos toda la información estructurada posible, algunos tienen más datos que otros
        tables = tornado_soup.find_all("table")
        tds = tables[0].find_all("td")
        for i in range(len(tds)):
            text = tds[i].get_text()
            if text == "State":
                state_value = tds[i + 1].get_text()
            elif text == "County/Area":
                county = tds[i + 1].get_text()
            elif text == "Report Source":
                report_source_value = tds[i + 1].get_text()
            elif text == "Begin Date":
                begin_date = tds[i + 1].get_text()
            elif text == "End Date":
                end_date = tds[i + 1].get_text()
            elif text == "Begin Lat/Lon":
                info == tds[i + 1].get_text().split("/")
                begin_lat = info[0]
                begin_lon = info[1]
            elif text == "End Lat/Lon":
                info = tds[i + 1].get_text().split("/")
                end_lat = info[0]
                end_lon = info[1]
            elif text == "Deaths Direct/Indirect":
                info = tds[i + 1].get_text().split(" ")[0].split("/")
                deaths_direct = info[0]
                deaths_indirect = info[1]
            elif text == "Injuries Direct/Indirect":
                info = tds[i + 1].get_text().split("/")
                injuries_direct = info[0]
                injuries_indirect = info[1]
            elif text == "-- Scale":
                scale = tds[i + 1].get_text()
            elif text == "-- Length":
                length = tds[i + 1].get_text().split(" ")[0]
            elif text == "-- Width":
                width = tds[i + 1].get_text().split(" ")[0]
            elif text == "Event Narrative":
                narrative = tds[i + 1].get_text()

        # Creamos nodos
        node1 = (prefix_ex.tornado + str(tornado_idx), RDF.type, prefix_st.Tornado)
        init_datetime_literal = Literal(begin_date, datatype=XSD.dateTime)
        end_datetime_literal = Literal(end_date, datatype=XSD.dateTime)
        node2 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.initDateTime, init_datetime_literal)
        node3 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.endDateTime, end_datetime_literal)

        state = (prefix_ex.tornado_state + str(tornado_idx), RDF.type, prefix_schema.State)
        state_address = Literal(state_value, datatype=prefix_schema.address)
        state_county = Literal(county, datatype=XSD.string)
        state2 = (prefix_ex.tornado_state + str(tornado_idx), prefix_schema.address, state_address)
        state3 = (prefix_ex.tornado_state + str(tornado_idx), prefix_ex.county, state_county)

        node4 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.state, prefix_ex.tornado_state + str(tornado_idx))
        if not 'scale' in locals():
            scale = "NotDefined"
            if scale == "EF0" or scale == "NotDefined":
                node5 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.enhancedFujitaScale, prefix_stf.F0)
            elif scale == "EF1":
                node5 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.enhancedFujitaScale, prefix_stf.F1)
            elif scale == "EF2":
                node5 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.enhancedFujitaScale, prefix_stf.F2)
            elif scale == "EF3":
                node5 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.enhancedFujitaScale, prefix_stf.F3)
            elif scale == "EF4":
                node5 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.enhancedFujitaScale, prefix_stf.F4)
            elif scale == "EF5":
                node5 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.enhancedFujitaScale, prefix_stf.F5)

        max_wind_speed = Literal("120", datatype=XSD.integer)

        wind_speed = (prefix_ex.max_wind_speed + str(tornado_idx), RDF.type, prefix_oum.Measure)
        wind_speed2 = (prefix_ex.max_wind_speed + str(tornado_idx), prefix_oum.hasNumericalValue, max_wind_speed)
        wind_speed3 = (prefix_ex.max_wind_speed + str(tornado_idx), prefix_oum.hasUnit, prefix_oum.mileStatutePerHour)

        node6 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.max_wind_speed, prefix_ex.max_wind_speed + str(tornado_idx))

        deaths_direct_literal = Literal(deaths_direct, datatype=XSD.integer)
        deaths_indirect_literal = Literal(deaths_indirect, datatype=XSD.integer)
        injuries_direct_literal = Literal(injuries_direct, datatype=XSD.integer)
        injuries_indirect_literal = Literal(injuries_indirect, datatype=XSD.integer)
        node7 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.deathsDirect, deaths_direct_literal)
        node8 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.deathsIndirect, deaths_indirect_literal)
        node9 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.injuriesDirect, injuries_direct_literal)
        node10 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.injuriesIndirect, injuries_indirect_literal)

        report_source = (prefix_ex.reportSource + str(tornado_idx), RDF.type, prefix_schema.Report)
        report_number_literal = Literal(report_source_value, datatype=prefix_schema.reportNumber)
        report_source2 = (prefix_ex.reportSource + str(tornado_idx), prefix_schema.reportNumber, report_number_literal)

        node11 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.reportSource, prefix_ex.report_source + str(tornado_idx))

        duration_literal = Literal("P0Y0M0DT0H20M0S", datatype=prefix_schema.Duration)
        node12 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.duration, duration_literal)

        begin_location_literal = Literal("2NE METAMORA", datatype=prefix_schema.beginLocation)
        node13 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.beginLocation, begin_location_literal)
        end_location_literal = Literal("2NE METAMORA", datatype=prefix_schema.endLocation)
        node14 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.endLocation, end_location_literal)

        if not 'begin_lat' in locals():
            begin_lat = 0
            begin_lon = 0
        init_coordinates = (prefix_ex.init_coordinates + str(tornado_idx), RDF.type, prefix_schema.GeoCoordinates)
        begin_latitude_literal = Literal(begin_lat, datatype=prefix_schema.latitude)
        begin_longitude_literal = Literal(begin_lon, datatype=prefix_schema.longitude)
        init_coordinates2 = (prefix_ex.init_coodinates + str(tornado_idx), prefix_ex.latitude, begin_latitude_literal)
        init_coordinates3 = (prefix_ex.init_coodinates + str(tornado_idx), prefix_ex.longitude, begin_longitude_literal)
        node15 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.init, prefix_ex.init_coordinates + str(tornado_idx))

        # Check it was defined, some events dont have this variable
        if not 'end_lat' in locals():
            end_lat = 0
            end_lon = 0

        end_coordinates = (prefix_ex.end_coordinates + str(tornado_idx), RDF.type, prefix_schema.GeoCoordinates)
        end_latitude_literal = Literal(end_lat, datatype=prefix_schema.latitude)
        end_longitude_literal = Literal(end_lon, datatype=prefix_schema.longitude)
        end_coordinates2 = (prefix_ex.end_coordinates + str(tornado_idx), prefix_ex.latitude, end_latitude_literal)
        end_coordinates3 = (prefix_ex.end_coordinates + str(tornado_idx), prefix_ex.longitude, end_longitude_literal)

        node16 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.end, prefix_ex.end_coordinates + str(tornado_idx))

        if not 'width' in locals():
            width = 0
            length = 0

        width_node = (prefix_ex.width + str(tornado_idx), RDF.type, prefix_oum.Measure)
        width_numerical_value_literal = Literal(width, datatype=XSD.double)
        width_node_2 = (prefix_ex.width + str(tornado_idx), prefix_oum.hasNumericalValue, width_numerical_value_literal)
        width_node_3 = (prefix_ex.width + str(tornado_idx), prefix_oum.hasUnit, prefix_oum.yardinternational)

        node17 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.width, prefix_ex.width_node + str(tornado_idx))

        length_node = (prefix_ex.length + str(tornado_idx), RDF.type, prefix_oum.Measure)
        length_numerical_value_literal = Literal(length, datatype=XSD.double)
        length_node_2 = (prefix_ex.length + str(tornado_idx), prefix_oum.hasNumericalValue, width_numerical_value_literal)
        length_node_3 = (prefix_ex.length + str(tornado_idx), prefix_oum.hasUnit, prefix_oum.mileStatute)

        node18 = (prefix_ex.tornado + str(tornado_idx), prefix_ex.width, prefix_ex.length_node + str(tornado_idx))

        # Open a graph in the open store and set identifier to default graph ID0.
        # Se añaden los nodos al grafo.
        graph.add((prefix_ex.listItem + str(tornado_idx), RDF.first, prefix_ex.tornado + str(tornado_idx)))
        graph.add(node1)
        graph.add(node2)
        graph.add(node3)
        graph.add(state)
        graph.add(state2)
        graph.add(state3)
        graph.add(node4)
        graph.add(node5)
        graph.add(wind_speed)
        graph.add(wind_speed2)
        graph.add(wind_speed3)
        graph.add(node6)
        graph.add(node7)
        graph.add(node8)
        graph.add(node9)
        graph.add(node10)
        graph.add(report_source)
        graph.add(report_source2)
        graph.add(node11)
        graph.add(node12)
        graph.add(node13)
        graph.add(node14)
        graph.add(init_coordinates)
        graph.add(init_coordinates2)
        graph.add(init_coordinates3)
        graph.add(node15)
        graph.add(end_coordinates)
        graph.add(end_coordinates2)
        graph.add(end_coordinates3)
        graph.add(node16)
        graph.add(width_node)
        graph.add(width_node_2)
        graph.add(width_node_3)
        graph.add(node17)
        graph.add(length_node)
        graph.add(length_node_2)
        graph.add(length_node_3)
        graph.add(node18)

        # Se procesan los eventos
        evento_idx = 0
        evento_max = 10
        # Event loop. La tabla de los enlaces a eventos es la última de la página
        a = tables[len(tables)-1].find_all("a")
        events = []
        # Se filtran los enlaces vacios (href="#")
        for event in a:
            if "eventdetails" in event.get("href"):
                events.append(event)
        # Si solo hay 1 es el mismo evento que se está analizando
        # Formateo de la lista en caso de que haya mas de un evento
        if len(events) > 1:
            graph.add((prefix_ex.tornado + str(tornado_idx), RDF.first,
                       prefix_ex.listItemEvento + str(tornado_idx) + str(evento_idx)))

            # Para cada evento se obtiene la info y se crean nodos
            for j in range(len(events)):
                if j < evento_max:
                    tornados_result = requests.get(url)
                    tornado_soup = BeautifulSoup(tornados_result.text, 'lxml')

                    tables = tornado_soup.find_all("table")
                    tds = tables[0].find_all("td")
                    for i in range(len(tds)):
                        text = tds[i].get_text()
                        if text == "State":
                            state_value = tds[i + 1].get_text()
                        elif text == "Event":
                            event_type = tds[i + 1].get_text()
                        elif text == "County/Area":
                            county = tds[i + 1].get_text()
                        elif text == "Report Source":
                            report_source_value = tds[i + 1].get_text()
                        elif text == "Begin Date":
                            begin_date = tds[i + 1].get_text()
                        elif text == "End Date":
                            end_date = tds[i + 1].get_text()
                        elif text == "Begin Lat/Lon":
                            info == tds[i + 1].get_text().split("/")
                            begin_lat = info[0]
                            begin_lon = info[1]
                        elif text == "End Lat/Lon":
                            info = tds[i + 1].get_text().split("/")
                            end_lat = info[0]
                            end_lon = info[1]
                        elif text == "Deaths Direct/Indirect":
                            info = tds[i + 1].get_text().split(" ")[0].split("/")
                            deaths_direct = info[0]
                            deaths_indirect = info[1]
                        elif text == "Injuries Direct/Indirect":
                            info = tds[i + 1].get_text().split("/")
                            injuries_direct = info[0]
                            injuries_indirect = info[1]
                        elif text == "-- Scale":
                            scale = tds[i + 1].get_text()
                        elif text == "-- Length":
                            length = tds[i + 1].get_text().split(" ")[0]
                        elif text == "-- Width":
                            width = tds[i + 1].get_text().split(" ")[0]
                        elif text == "Event Narrative":
                            narrative = tds[i + 1].get_text()

                    # Se crean los nodos
                    type_literal = Literal(event_type, datatype=XSD.string)
                    node1 = (prefix_ex.evento + str(tornado_idx) + str(evento_idx), prefix_ex.type, type_literal)

                    init_datetime_literal = Literal(begin_date, datatype=XSD.dateTime)
                    end_datetime_literal = Literal(end_date, datatype=XSD.dateTime)
                    node2 = (prefix_ex.evento + str(tornado_idx) + str(evento_idx), prefix_ex.initDateTime, init_datetime_literal)
                    node3 = (prefix_ex.evento + str(tornado_idx) + str(evento_idx), prefix_ex.endDateTime, end_datetime_literal)

                    state = (prefix_ex.evento_state + str(tornado_idx) + str(evento_idx), RDF.type, prefix_schema.State)
                    state_address = Literal(state_value, datatype=prefix_schema.address)
                    state_county = Literal(county, datatype=XSD.string)
                    state2 = (prefix_ex.evento_state + str(tornado_idx) + str(evento_idx), prefix_schema.address, state_address)
                    state3 = (prefix_ex.evento_state + str(tornado_idx) + str(evento_idx), prefix_ex.county, state_county)

                    node4 = (prefix_ex.evento + str(tornado_idx) + str(evento_idx), prefix_ex.state, prefix_ex.evento_state + str(tornado_idx) + str(evento_idx))


                    deaths_direct_literal = Literal(deaths_direct, datatype=XSD.integer)
                    deaths_indirect_literal = Literal(deaths_indirect, datatype=XSD.integer)
                    injuries_direct_literal = Literal(injuries_direct, datatype=XSD.integer)
                    injuries_indirect_literal = Literal(injuries_indirect, datatype=XSD.integer)
                    node5 = (prefix_ex.evento + str(tornado_idx) + str(evento_idx), prefix_ex.deathsDirect, deaths_direct_literal)
                    node6 = (prefix_ex.evento + str(tornado_idx) + str(evento_idx), prefix_ex.deathsIndirect, deaths_indirect_literal)
                    node7 = (prefix_ex.evento + str(tornado_idx) + str(evento_idx), prefix_ex.injuriesDirect, injuries_direct_literal)
                    node8 = (prefix_ex.evento + str(tornado_idx) + str(evento_idx), prefix_ex.injuriesIndirect, injuries_indirect_literal)

                    report_source = (prefix_ex.reportSource + str(tornado_idx) + str(evento_idx), RDF.type, prefix_schema.Report)
                    report_number_literal = Literal(report_source_value, datatype=prefix_schema.reportNumber)
                    report_source2 = (prefix_ex.reportSource + str(tornado_idx) + str(evento_idx), prefix_schema.reportNumber, report_number_literal)

                    node9 = (prefix_ex.evento + str(tornado_idx) + str(evento_idx), prefix_ex.reportSource, prefix_ex.report_source + str(tornado_idx) + str(evento_idx))

                    begin_location_literal = Literal("2NE METAMORA", datatype=prefix_schema.beginLocation)
                    node10 = (prefix_ex.evento + str(tornado_idx) + str(evento_idx), prefix_ex.beginLocation, begin_location_literal)
                    end_location_literal = Literal("2NE METAMORA", datatype=prefix_schema.endLocation)
                    node11 = (prefix_ex.evento + str(tornado_idx) + str(evento_idx), prefix_ex.endLocation, end_location_literal)

                    # Open a graph in the open store and set identifier to default graph ID.
                    # Se añaden los nodos al grafo
                    graph.add((prefix_ex.listItemEvento + str(tornado_idx) + str(evento_idx), RDF.first, prefix_ex.evento + str(tornado_idx) + str(evento_idx)))
                    graph.add(node1)
                    graph.add(node2)
                    graph.add(node3)
                    graph.add(state)
                    graph.add(state2)
                    graph.add(state3)
                    graph.add(node4)
                    graph.add(node5)
                    graph.add(node7)
                    graph.add(node8)
                    graph.add(node9)
                    graph.add(node10)
                    graph.add(report_source)
                    graph.add(report_source2)
                    graph.add(node11)
                    # Formateo de la lista de eventos final
                    if evento_idx < len(events):
                        graph.add((prefix_ex.listItemEvento + str(tornado_idx) + str(evento_idx), RDF.rest, prefix_ex.listItemEvento + str(tornado_idx) + str(evento_idx + 1)))
                    else:
                        graph.add((prefix_ex.listItemEvento + str(tornado_idx) + str(evento_idx), RDF.rest, RDF.nil))
                    evento_idx = evento_idx + 1
        # Rest if there are more
        # Formateo de la lista de tornados final
        if tornado_idx < len(link_list):
            graph.add((prefix_ex.listItem + str(tornado_idx), RDF.rest, prefix_ex.listItem + str(tornado_idx + 1)))
        # Rest if there are no more
        else:
            graph.add((prefix_ex.listItem + str(tornado_idx), RDF.rest, RDF.nil))
        tornado_idx = tornado_idx + 1

    # Se guarda el grafo en fuseki.
    store.add_graph(graph)
