# Structured logging data model

## Common

<table>
    <th>Name</th>
    <th>Description</th>
    <th>Data type</th>
    <tr>
        <td>count</td>
        <td>Number of elements</td>
        <td>int</td>
    </tr>
    <tr>
        <td>reason</td>
        <td>Reason of event (e.g. exception message)</td>
        <td>str</td>
    </tr>
</table>

## Network

<table>
    <th>Name</th>
    <th>Description</th>
    <th>Data type</th>
    <tr>
        <td>ip</td>
        <td>IP address</td>
        <td>str</td>
    </tr>
    <tr>
        <td>port</td>
        <td>Port number</td>
        <td>int</td>
    </tr>
    <tr>
        <td>request_info</td>
        <td>Information about request</td>
        <td>str</td>
    </tr>
    <tr>
        <td>url</td>
        <td>URL address</td>
        <td>str</td>
    </tr>
    <tr>
        <td>http_status</td>
        <td>HTTP response code</td>
        <td>int</td>
    </tr>
</table>

## OS

<table>
    <th>Name</th>
    <th>Description</th>
    <th>Data type</th>
    <tr>
        <td>file_path</td>
        <td>Path to file</td>
        <td>str</td>
    </tr>
</table>

## Plugins

<table>
    <th>Name</th>
    <th>Description</th>
    <th>Data type</th>
    <tr>
        <td>plugin_type</td>
        <td>Type of plugin (e.g. "input", "event" etc.)</td>
        <td>str</td>
    </tr>
    <tr>
        <td>plugin_name</td>
        <td>Name of plugin (e.g. "cron")</td>
        <td>str</td>
    </tr>
    <tr>
        <td>plugin_id</td>
        <td>ID of plugin instance</td>
        <td>int</td>
    </tr>
    <tr>
        <td>plugin_class</td>
        <td>Class of the plugin (shown during registration process)</td>
        <td>str</td>
    </tr>
    <tr>
        <td>plugin_config_class</td>
        <td>Class of the plugin config (shown during registration process)</td>
        <td>str</td>
    </tr>
</table>

### Input plugins

<table>
    <th>Name</th>
    <th>Description</th>
    <th>Data type</th>
    <tr>
        <td>first_timestamp</td>
        <td>First timestamp in some collection (e.g in batch) in ISO8601 format</td>
        <td>str</td>
    </tr>
    <tr>
        <td>last_timestamp</td>
        <td>Last timestamp in some collection (e.g in batch) in ISO8601 format</td>
        <td>str</td>
    </tr>
    <tr>
        <td>start_timestamp</td>
        <td>Start timestamp of plugin generation in ISO8601 format</td>
        <td>str</td>
    </tr>
    <tr>
        <td>end_timestamp</td>
        <td>End timestamp of plugin generation in ISO8601 format</td>
        <td>str</td>
    </tr>
</table>

### Event plugins

#### Jinja Event plugin

<table>
    <th>Name</th>
    <th>Description</th>
    <th>Data type</th>
    <tr>
        <td>template_alias</td>
        <td>Alias of template</td>
        <td>str</td>
    </tr>
</table>

### Output plugins

<table>
    <th>Name</th>
    <th>Description</th>
    <th>Data type</th>
    <tr>
        <td>format</td>
        <td>Format of outcome event (e.g. "plain", "ndjson" etc.)</td>
        <td>str</td>
    </tr>
    <tr>
        <td>original_event</td>
        <td>Original unformatted event</td>
        <td>str</td>
    </tr>
</table>
