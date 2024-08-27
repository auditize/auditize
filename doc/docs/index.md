# Auditize

Auditize is a comprehensive audit log solution designed to seamlessly integrate auditability into your software. It combines powerful features with ease of integration to enhance your application’s tracability.

<!-- It features:

- A REST API for pushing audit logs and managing Auditize
- A web interface to manage Auditize
- A log consultation interface with search capabilities and saveable filters
- A web component to integrate the log consultation interface right into your own web interface
- Multi-tenancy support
- A rich and flexible log model
- Internationalization support -->

<div class="adz-intros">
  <div class="adz-intro">
    <div class="adz-intro-text">
      <a href="sending-logs">
        <h2>REST API</h2>
        Send your logs to Auditize using an easy-to-use REST API.
      </a>
    </div>
    <div class="adz-intro-image">
      <img src='/assets/intro-send-log-curl.png' width="649" height="154"/>
    </div>
  </div>

  <div class="adz-intro">
    <div class="adz-intro-text">
      <a href="overview#log-repositories">
        <h2>Multi-tenancy</h2>
        Partition your logs using log repositories. Each repository use its own database, and users and API keys can be granted different permissions on a specific set of repositories.
      </a>
    </div>
    <div class="adz-intro-image">
      <img src='/assets/repositories.png' width="532" height="296"/>
    </div>
  </div>

  <div class="adz-intro">
    <div class="adz-intro-text">
      <h2>Log UI</h2>
      Explore your logs with advanced search criteria, saveable filters, CSV export, and more.
    </div>
    <div class="adz-intro-image">
      <img src='/assets/intro-log-ui.png' width="598" height="238"/>
    </div>
  </div>

  <div class="adz-intro">
    <div class="adz-intro-text">
      <a href="overview#log-i18n-profiles">
        <h2>Internationalization</h2>
        Auditize is available in multiple languages and also supports internationalization of your logs through translation profiles.
      </a>
    </div>
    <div class="adz-intro-image">
      <img src='/assets/intro-log-ui-fr.png' width="599" height="381"/>
    </div>
  </div>

  <div class="adz-intro">
    <div class="adz-intro-text">
      <a href="logs#entity_path">
        <h2>Entity Mapping</h2>
        Map your own organisational entities into Auditize. Entities can be anything: a customer, an organizational unit, a geographical location, etc. They can be used for log filtering but also to restrict user access to certain log entities.
      </a>
    </div>
    <div class="adz-intro-image">
      <img src='/assets/intro-log-entities.png' width="536" height="340"/>
    </div>
  </div>

  <div class="adz-intro">
    <div class="adz-intro-text">
      <a href="logs">
        <h2>Log data model</h2>
        <p>Auditize features a rich and flexible log data model. Given a base set of fields that allow you to describe the actor, the action, the resource, tags, etc. you can extend the actor and resource fields with custom fields. Source and details fields which are fully customizable allow you to provide additional context to the log.</p>
        <p>Files can also be attached to logs.</p>
      </a>
    </div>
    <div class="adz-intro-image">
      <img src='/assets/intro-log-data-model.png' width="368" height="486"/>
    </div>
  </div>

  <div class="adz-intro">
    <div class="adz-intro-text">
      <a href="web-component">
        <h2>Web Component</h2>
        Integrate the log interface right into your application frontend using a Web Component.
      </a>
    </div>
    <div class="adz-intro-image">
      <img src='/assets/intro-web-component-integration.png' width="528" height="284"/>
    </div>
  </div>

  <div class="adz-intro">
    <div class="adz-intro-text">
      <a href="api.html">
        <h2>OpenAPI</h2>
        Entire Auditize REST API is documented using OpenAPI.
      </a>
    </div>
    <div class="adz-intro-image">
      <img src='/assets/intro-openapi.png' width="543" height="409"/>
    </div>
  </div>
</div>