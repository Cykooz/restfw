.. raw:: html

  <link rel="stylesheet" href="../../../_static/schema/json-formatter.min.css">
  <link rel="stylesheet" href="../../../_static/schema/json-schema-view.css">
  <script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.3.15/angular.js"></script>
  <script src="../../../_static/schema/json-formatter.min.js"></script>
  <script src="../../../_static/schema/json-schema-view.js"></script>
  <script src="../../../_static/schema/json-schema-view-body.js"></script>
  <script src="../../../_static/schema/schema.js"></script>
  <div ng-app="schemaview" ng-controller="SchemaCtrl">

{{ entry_point.name|rst_header('*') }}

**Resource class:** {{ entry_point.resource_class }}

{{ resource_doc }}

{{ entry_point.doc }}

.. raw:: html

  </div>
