<h1>meshtasticmap</h1>
<p>Scan a channel for location data and display it on a map.</p>

<p>Download the python script and make it executable:</p>
<p><code>chmod +x meshtasticmap.py</code></p>
<p>Use your favorite editor to update your channel and node configuration:</p>
<p><code>nano meshtasticmap.py</code></p>
<p>Change ENCRYPTED_CHANNEL, CHANNEL_NAME, and HOST to your information. The nodes must be configured to allow MQTT and the node your connecting to that collects the data must be on the same network</p>
<p>The script depends on folium so you're gonnna need to install that</p>
<p><code>pip install folium</code></p>
<p>Now run the script</p>
<p><code>./meshtasticmap.py</code></p>
The script will add nodes to a map on a webpage located in the same directory called node_map.html
