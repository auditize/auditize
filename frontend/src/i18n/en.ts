export default {
  navigation: {
    management: "Management",
    repositories: "Repositories",
    users: "Users",
    apikeys: "API Keys",
    logs: "Logs",
    logi18nprofiles: "Log translations",
    preferences: "Preferences",
    logout: "Logout",
  },
  language: {
    fr: "French",
    en: "English",
  },
  repo: {
    repo: "Repository",
    repos: "Repositories",
    storage: "Storage",
    lastLog: "Last log",
    form: {
      name: {
        label: "Name",
        placeholder: "Repository name",
        required: "Repository name is required.",
      },
      logI18nProfile: {
        label: "Translations",
        placeholder: "Select a log translation profile",
      },
      retentionPeriod: {
        label: "Retention period",
        placeholder: "Retention period in days",
      },
      status: {
        label: "Status",
        value: {
          enabled: "Enabled",
          readonly: "Read-only",
          disabled: "Disabled",
        },
      },
    },
    create: {
      title: "Create a repository",
    },
    edit: {
      title: "Edit repository",
    },
    list: {
      title: "Repositories",
      column: {
        name: "Name",
        id: "ID",
        status: "Status",
        retentionPeriod: "Retention",
        retentionPeriodValue: "{{days}}d",
        logs: "Logs",
        storage: "Storage",
        createdAt: "Created At",
        lastLog: "Last Log",
      },
    },
    delete: {
      confirm:
        "Do you confirm the deletion of the log repository <1>{{name}}</1>?",
    },
  },
  logi18nprofile: {
    logi18nprofile: "Translation profile",
    logi18nprofiles: "Log translation profiles",
    form: {
      name: {
        label: "Name",
        placeholder: "Profile name",
        required: "The profile name is required.",
      },
      file: {
        label: "Translation file for: {{lang}}",
        choose: "Select file",
        configured: "Translation configured",
      },
    },
    create: {
      title: "Create a log translation profile",
    },
    edit: {
      title: "Edit log translation profile",
    },
    list: {
      title: "Log translations",
      column: {
        name: "Name",
        createdAt: "Created at",
        langs: "Languages",
      },
    },
    delete: {
      confirm:
        "Do you confirm the deletion of the log translation profile <1>{{name}}</1>?",
    },
  },
  user: {
    user: "User",
    form: {
      firstName: {
        label: "First Name",
        placeholder: "User's first name",
        required: "First name is required.",
      },
      lastName: {
        label: "Last Name",
        placeholder: "User's last name",
        required: "Last name is required.",
      },
      email: {
        label: "Email",
        placeholder: "User's email",
        required: "Email is invalid.",
      },
      language: {
        label: "Language",
      },
    },
    list: {
      title: "Users",
      column: {
        name: "Name",
        email: "Email",
        permissions: "Permissions",
      },
    },
    create: {
      title: "Create a user",
    },
    edit: {
      title: "Edit user",
    },
    delete: {
      confirm: "Do you confirm the deletion of the user <1>{{name}}</1>?",
    },
  },
  apikey: {
    apikey: "API Key",
    list: {
      title: "API Keys",
      column: {
        name: "Name",
        permissions: "Permissions",
      },
    },
    form: {
      name: {
        label: "Name",
        placeholder: "Key name",
        required: "Key name is required.",
      },
      key: {
        label: "Secret Key",
        placeholder: {
          create: "The secret will be displayed once the key has been saved",
          update:
            "You can generate a new secret by clicking the refresh button",
        },
      },
    },
    create: {
      title: "Create an API key",
    },
    edit: {
      title: "Edit API key",
    },
    delete: {
      confirm: "Do you confirm the deletion of the API key <1>{{name}}</1>?",
    },
  },
  log: {
    log: "Log",
    logs: "Logs",
    date: "Date",
    dateFrom: "From",
    dateTo: "To",
    action: "Action",
    actionCategory: "Action category",
    actionType: "Action type",
    actor: "Actor",
    actorType: "Actor type",
    actorName: "Actor name",
    actorRef: "Actor ref.",
    source: "Source",
    resource: "Resource",
    resourceType: "Resource type",
    resourceName: "Resource name",
    resourceRef: "Resource ref.",
    details: "Details",
    tag: "Tag",
    tags: "Tags",
    tagType: "Tag type",
    tagTypes: "Tag types",
    tagName: "Tag name",
    tagNames: "Tag names",
    tagRef: "Tag refs.",
    tagRefs: "Tag refs.",
    hasAttachment: "Has attachment",
    attachment: "Attachment",
    attachments: "Attachments",
    attachmentType: "Attachment type",
    attachmentTypes: "Attachment types",
    attachmentMimeType: "Attachment MIME type",
    attachmentMimeTypes: "Attachment MIME types",
    attachmentName: "Attachment name",
    attachmentNames: "Attachment names",
    attachmentRef: "Attachment ref.",
    attachmentRefs: "Attachment refs.",
    downloadAttachment: "Download attachment",
    entity: "Entity",
    list: {
      columnSelector: {
        reset: "Reset columns",
      },
      searchParams: {
        apply: "Apply",
        clear: "Clear",
      },
      documentTitle: "Logs",
      noResults: "No results",
      noRepos: "No repositories have been created yet.",
      loadMore: "Load more",
      untilMustBeGreaterThanSince:
        "The end date must be greater than the start date",
    },
    view: {
      name: "Name",
      type: "Type",
      ref: "Reference",
    },
    csv: {
      csv: "CSV",
      csvExportDefault: "Export as CSV (default columns)",
      csvExportCurrent: "Export as CSV (selected columns)",
    },
    filter: {
      filter: "Filter",
      filters: "Filters",
      save: "Save filter",
      update: "Update current filter",
      updateError: "Unable to update filter",
      updateSuccess: "The filter has been updated",
      manage: "Manage filters",
      dirty: "Filter has unsaved changes",
      form: {
        name: {
          label: "Name",
          placeholder: "Filter name",
          required: "Filter name is required.",
        },
      },
      create: {
        title: "Save log filter",
      },
      edit: {
        title: "Edit log filter",
      },
      delete: {
        confirm: "Do you confirm the deletion of filter <1>{{name}}</1>?",
      },
      list: {
        title: "Log Filters",
        column: {
          name: "Name",
        },
        apply: "Apply filter",
      },
    },
    inlineFilter: {
      filterOn: "Filter on {{field}}",
      field: {
        actor: "this actor",
        actorType: "this actor's type",
        actorRef: "this actor's ref.",
        actorName: "this actor's name",
        actorCustomField: "this actor's {{field}}",
        actionType: "this action type",
        actionCategory: "this action category",
        resource: "this resource",
        resourceType: "this resource's type",
        resourceRef: "this resource's ref.",
        resourceName: "this resource's name",
        resourceCustomField: "this resource's {{field}}",
        tag: "this tag",
        tagType: "this tag's type",
        tagName: "this tag's name",
        tagRef: "this tag's ref.",
        attachmentType: "this attachment's type",
        attachmentMimeType: "this MIME type",
        attachmentName: "this attachment's name",
        entity: "this entity",
        sourceField: "this {{field}}",
        detailField: "this {{field}}",
      },
    },
  },
  permission: {
    tab: {
      general: "General",
      permissions: "Permissions",
    },
    read: "Read",
    write: "Write",
    superadmin: "Superadmin (all permissions)",
    management: "Management",
    repositories: "Repositories",
    users: "Users",
    apikeys: "API Keys",
    logs: "Logs",
    allRepos: "All repositories",
    entities: "Entities",
    summary: {
      read: "read",
      write: "write",
      readwrite: "rw",
      partial: "partial",
      superadmin: "Superadmin",
    },
  },
  common: {
    name: "Name",
    id: "ID",
    status: "Status",
    createdAt: "Created at",
    copy: "Copy",
    copied: "Copied !",
    enabled: "Enabled",
    disabled: "Disabled",
    readonly: "Read-only",
    save: "Save",
    cancel: "Cancel",
    confirm: "Confirm",
    submit: "Submit",
    delete: "Delete",
    close: "Close",
    clear: "Clear",
    ok: "Ok",
    loading: "Loading...",
    noData: "No data",
    notCurrentlyAvailable: "Not currently available",
    unexpectedError: "An error occurred",
    send: "Send",
    scrollToTop: "Scroll to top",
    moreDetails: "More details",
    lessDetails: "Less details",
    chooseAValue: "Choose a value",
    passwordForm: {
      password: {
        label: "Password",
        placeholder: "Password",
        required: "Password is required.",
        tooShort: "Password must be at least {{min}} characters long.",
      },
      passwordConfirmation: {
        label: "Password confirmation",
        placeholder: "Password confirmation",
        doesNotMatch: "Passwords do not match.",
      },
    },
    error: {
      error: "Error",
      details: "Error: {{error}}",
      unexpected: "An unexpected error occurred.",
      401: "Authentication error",
      403: "Error: Permission denied",
    },
  },
  resource: {
    list: {
      search: "Search",
      delete: "Delete",
    },
    edit: {
      save: "Save",
      cancel: "Cancel",
    },
    delete: {
      confirm: {
        title: "Confirm deletion",
      },
    },
  },
  accountSettings: {
    title: "Account Settings",
    tab: {
      general: "General",
      password: "Password",
    },
    form: {
      lang: {
        label: "Language",
      },
    },
  },
  logout: {
    title: "Confirm logout",
    confirm: "Do you really want to log out?",
    expiration: "Your session has expired, you need to log in again.",
  },
  login: {
    title: "Login",
    welcome: "Welcome to Auditize",
    form: {
      email: {
        label: "Email",
        placeholder: "Your email",
        invalid: "Invalid email",
      },
      password: {
        label: "Password",
        placeholder: "Your password",
      },
    },
    signIn: "Login",
    invalidCredentials: "Invalid email or password. Please try again.",
  },
  forgotPassword: {
    link: "I forgot my password",
    title: "Ask for a password reset",
    description: "Enter your email address to receive a password reset link.",
    emailSent:
      "A password reset link has been sent to your email address (if your email address is correct).",
    form: {
      email: {
        label: "Email",
        placeholder: "Your email",
        invalid: "Invalid email",
      },
    },
  },
  passwordSetup: {
    form: {
      firstName: {
        label: "First Name",
      },
      lastName: {
        label: "Last Name",
      },
      email: {
        label: "Email",
      },
    },
    accountSetup: {
      title: "Set up your account",
      success: "The setup of your user account is now complete.",
    },
    passwordReset: {
      title: "Reset your Auditize password",
      success: "Your password has been successfully updated.",
    },
    loginLink: "You can now log in by <1>clicking on this link</1>.",
    documentTitle: "Password Change",
  },
};
