/*
// Parse a SPARQL query to a JSON object
var SparqlParser = require('sparqljs').Parser;
var parser = new SparqlParser();
var parsedQuery = parser.parse(
  'PREFIX foaf: <http://156.35.98.103:3030/tornados/sparql> ' +
  'SELECT distinct ?s ?p ?o WHERE { ?s ?p ?o }');

// Regenerate a SPARQL query from a JSON object
var SparqlGenerator = require('sparqljs').Generator;
var generator = new SparqlGenerator({  });
//parsedQuery.variables = ['?mickey'];
var generatedQuery = generator.stringify(parsedQuery);

console.log(generatedQuery)

*/
//var query= "SELECT distinct ?s ?p ?o WHERE { ?s ?p ?o. }"; //FILTER (?s = 'b51'). 

var query= "SELECT distinct ?s ?p ?o WHERE { graph ?g{ ?s ?p ?o} }";
var queryUrl = "http://156.35.98.103:3030/tornados/sparql?query=" + encodeURIComponent(query) + "&format=json";
var tornadosList = {}
var actualTornado = -1

var smallestTornado = "0"
var biggestTornado = "0"

function containsAnyLetter(str) {
  return /[a-zA-Z]/.test(str);
}

function searchTornados(reporter){
  tornadosList = {}
  var gotFirstTornado = false
  $.ajax({
      dataType: "jsonp",
      url: queryUrl,
      success: function (_data) {
          var results = _data.results.bindings;
          var idactual = 0
          for (var i in results) {
              
              if (results[i].o.type == 'literal' && results[i].s.type == 'uri') {
                var removeurl = results[i].s.value.replace('http://example.org/tornado','');
                
                //solo los de twitter
                if (!containsAnyLetter(removeurl)) {
                  if (parseInt(removeurl) >= 10000){
                    tornadosList[removeurl] = {}
                    idactual = removeurl

                    if (!gotFirstTornado) {
                      gotFirstTornado = true
                      smallestTornado = idactual
                    }

                    
                    //como el value de s es numerico tenemos que chequear aqui la fecha
                    if (results[i].o.datatype.includes("http://www.w3.org/2001/XMLSchema#")) {
                      //datetime
                      tornadosList[idactual]["dateTime"] = results[i].o.value
                      tornadosList[idactual]["id"] = idactual
                    }
                  }
                }
                else {
                  
                  if (tornadosList[idactual]) { //si no esta es que no cumplia el filtro
                    var lastFive = removeurl.substr(removeurl.length - 5);

                    if (!containsAnyLetter(lastFive)) {
                      if (results[i].o.datatype != undefined) {
                        
                        if (results[i].o.datatype.includes("http://schema.org/")) {
                          //reportNumber
                          //longitude
                          //latitude
                          var tipoDato = results[i].o.datatype.replace('http://schema.org/','');
                          if (results[i].o.value != undefined) {
                            tornadosList[idactual][tipoDato] = results[i].o.value


                            //filtro
                            if (tipoDato == 'reportNumber')
                              if (!(results[i].o.value.includes(reporter)) && reporter.length > 0){
                                delete tornadosList[idactual]
                              }
                              else {
                                biggestTornado = idactual //guardamos siempre el de mayor valor
                              }
                          }
                        }
                      }
                    }
                  }
                }
                
              }


          }
          console.log(tornadosList)


          //establecemos los valores del primer tornado
          //recogemos primer y ultimo indice para botones

          var conteoitems = 0

          for (var i in tornadosList) {
            if (tornadosList.hasOwnProperty(i)) conteoitems++;
          }
          if (conteoitems > 0) {
            var primerakey = Object.keys(tornadosList)[0];

            actualTornado = primerakey

            console.log(primerakey)
            
            document.getElementById('idLabel').innerHTML = "Id Tornado: " + tornadosList[primerakey]["id"]
            document.getElementById('reporterLabel').innerHTML = "Tornado Reporter: " + tornadosList[primerakey]["reportNumber"]
            document.getElementById('coordsLabel').innerHTML = "Latitud, Longitud: (" + tornadosList[primerakey]["latitude"] + ", " + tornadosList[primerakey]["longitude"] + ")"
            document.getElementById('dateLabel').innerHTML = "Fecha: " + tornadosList[primerakey]["dateTime"]

            document.getElementById('iframecoords').src = 'https://maps.google.com/maps?q=' + tornadosList[actualTornado]["latitude"] + ',' + tornadosList[actualTornado]["longitude"] + '&hl=es&z=14&amp&output=embed'
          }
          else {
            document.getElementById('idLabel').innerHTML = "Id Tornado: "
            document.getElementById('reporterLabel').innerHTML = "Tornado Reporter: "
            document.getElementById('coordsLabel').innerHTML = "Latitud, Longitud:"
            document.getElementById('dateLabel').innerHTML = "Fecha: "

            document.getElementById('iframecoords').src = 'https://maps.google.com/maps?q=0,0&hl=es&z=14&amp&output=embed'

          }
      }
  });
}

function findLast(key, obj) {
  var keys = Object.keys(obj);

  var esto = keys[(keys.indexOf(key) - 1) % keys.length] + ""

  return esto
  
}

function lastTornado(){

  var conteoitems = 0

  for (var i in tornadosList) {
    if (tornadosList.hasOwnProperty(i)) conteoitems++;
  }
  if (conteoitems > 0) {


    actualTornado = findLast(actualTornado, tornadosList)

    //check para que no pete
    if (actualTornado == "undefined") {
      actualTornado = biggestTornado
      
    }

    document.getElementById('idLabel').innerHTML = "Id Tornado: " + tornadosList[actualTornado]["id"]
    document.getElementById('reporterLabel').innerHTML = "Tornado Reporter: " + tornadosList[actualTornado]["reportNumber"]
    document.getElementById('coordsLabel').innerHTML = "Latitud, Longitud: (" + tornadosList[actualTornado]["latitude"] + ", " + tornadosList[actualTornado]["longitude"] + ")"
    document.getElementById('dateLabel').innerHTML = "Fecha: " + tornadosList[actualTornado]["dateTime"]

    document.getElementById('iframecoords').src = 'https://maps.google.com/maps?q=' + tornadosList[actualTornado]["latitude"] + ',' + tornadosList[actualTornado]["longitude"] + '&hl=es&z=14&amp&output=embed'
  }
}

function findNext(key, obj) {
  var keys = Object.keys(obj);

  var esto = keys[(keys.indexOf(key) + 1) % keys.length] + ""

  return esto
  
}

function nextTornado(){
  var conteoitems = 0

  for (var i in tornadosList) {
    if (tornadosList.hasOwnProperty(i)) conteoitems++;
  }
  if (conteoitems > 0) {

    actualTornado = findNext(actualTornado, tornadosList)

    document.getElementById('idLabel').innerHTML = "Id Tornado: " + tornadosList[actualTornado]["id"]
    document.getElementById('reporterLabel').innerHTML = "Tornado Reporter: " + tornadosList[actualTornado]["reportNumber"]
    document.getElementById('coordsLabel').innerHTML = "Latitud, Longitud: (" + tornadosList[actualTornado]["latitude"] + ", " + tornadosList[actualTornado]["longitude"] + ")"
    document.getElementById('dateLabel').innerHTML = "Fecha: " + tornadosList[actualTornado]["dateTime"]

    document.getElementById('iframecoords').src = 'https://maps.google.com/maps?q=' + tornadosList[actualTornado]["latitude"] + ',' + tornadosList[actualTornado]["longitude"] + '&hl=es&z=14&amp&output=embed'
  }
}

/*
   let keys = Object.keys(storeObject);
 let nextIndex = keys.indexOf(theCurrentItem) +1;
 let nextItem = keys[nextIndex];
*/