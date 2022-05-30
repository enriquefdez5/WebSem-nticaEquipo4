# WebSemánticaEquipo4
Repositorio con el contenido de los ejercicios realizados para la práctica de Web Semántida del Master en Ingeniería Web de la Universidad de Oviedo por el equipo 4 formado por Enrique Fernández Manzano, Sergio Domínguez Cabrero y Sergio Berjano Salinas.


## Ejercicio 1. Crear grafo de conocimiento con información sobre tornados.
La carpeta de este ejercicio contiene un fichero con extensión ttl que contiene un grafo de tornados con eventos.
También contiene un fichero con extensión shex cuyo contenido es un conjunto de shape expressions para validar el grafo de tornados previamente realizado.
El endpoint se encuentra en http://156.35.98.103:3030. Si está apagada mandar correo a uo257742@uniovi.es para levantar la triplestore.

## Ejercicio 2. Rellenar el grafo de conocimiento con datos estructurados.
La carpeta de este ejercicio contiene un script de python en el que se realiza una petición a la web de NOAA de tormentas. Se procesa esa petición y mediante web scrapping se accede a la información de los tornados estructurada en tablas.  

## Ejercicio 3. Rellenar el grafo de conocimiento con datos en lenguaje natural.
Este ejercicio está formado por un script similar al del ejercicio 2 en el que se procesa una colección de ficheros html para obtener la narrativa de unos tornados y obtener información acerca de ellos. Al no estar identificados ha sido imposible referenciar a tornados de la triplestore ya creados, por lo que se han añadido como nuevos tornados. 
Se ha realizado NLP sobre la narrativa para cada tornado y se ha obtenido velocidad del viento en mph y rutas y lugares de interés que aparecían referenciados.
El proceso seguido se puede ver en el siguiente Colab: https://colab.research.google.com/drive/1I0GBjW5UgWos-j7f-avVLXXsx66hO8vi#scrollTo=uD0c5yiiMvuP (No es posible ejecutar la parte del grafo ya que se necesita estar en la VPN de la Universidad para la conexión con la máquina)

## Ejercicio 4. Rellenar el grafo de conocimiento con datos de Twitter.
La carpeta contiene un script en python y el zip con la colección de tweets que se ha analizado.
Primero se ha realizado un análisis de los tweets.
- Se ha visto que están comprendidos entre el 25 y 30 de Mayo de 2019.
- Se ha realizado NER, KWIC y búsqueda de tripletas para obtener información.
  - Se ha visto que Oklahoma, Kansas y Texas son los lugares más mencionados, hay una gran cantidad de avisos de tornados, se mencionan velocidades y daños, poca información sobre heridos y muertos y poca información específica sobre los detalles del tornado(nivel de inundación, granizo, etc...)
- Se ha filtrado la colección para obtener los tweets de usuarios verificados.
- Se han eliminado duplicados.
- Se ha procesado la fecha del tweet, las coordenadas y lugar de los tweets georeferenciados y el nombre de usuario como fuente de información.
- Se ha visto que el 75% de los tweets eran de una fuente del NWS.
- Se ha visto que el 50% de los tweets eran de la fuente de NWS Severe Storm.
- El texto de los tweets restantes era bastante pobre y ofrecía poca información sobre los detalles de los tornados.

Por cada tuit se ha añadido un torndado, aunque lo más seguro que, al ser tan cercanos en el tiempo y sobre lugares concretos muy mencionados (Oklahoma, KS, Texas...) seguramente sean el mismo tornado con varios eventos. No hemos podido/sabido como demostrarlo ni nos ha dado tiempo para más.

El proceso seguido se puede ver en el siguiente Colab: https://colab.research.google.com/drive/14Rue87-xn6wKDB4c9alnPlsrQuSzJ3JH?hl=es (No es posible ejecutar la parte del grafo ya que se necesita estar en la VPN de la Universidad para la conexión con la máquina)

## Ejercicio 5 Investigación. 
En esta carpeta se encuentra el poster en formato ppt y svg realizado.


## Ejercicio 5 Profesional - UO250788. 
En esta carpeta se encuentra el sitio web realizado para el susodicho ejercicio por Sergio Domínguez Cabrero. EL sitio web permite búsqueda de tornados por reporter y visualización en Google Maps.
