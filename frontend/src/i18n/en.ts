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
    logi18nprofile: "Log translation profile",
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
    node: "Node",
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
      csvExportDefault: "Export as CSV (all builtin columns)",
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
        title: "My Filters",
        column: {
          name: "Name",
        },
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
    summary: {
      read: "read",
      write: "write",
      readwrite: "rw",
      partial: "partial",
      none: "None",
      superadmin: "Superadmin",
    },
  },
  common: {
    name: "Name",
    id: "ID",
    status: "Status",
    createdAt: "Created at",
    copy: "Copy",
    copied: "Copied",
    enabled: "Enabled",
    disabled: "Disabled",
    readonly: "Read-only",
    error: "Error: {{error}}",
    save: "Save",
    cancel: "Cancel",
    confirm: "Confirm",
    submit: "Submit",
    delete: "Delete",
    close: "Close",
    ok: "Ok",
    loading: "Loading...",
    notAvailable: "Not available",
    notCurrentlyAvailable: "Not currently available",
    unexpectedError: "An error occurred",
    send: "Send",
  },
  resource: {
    list: {
      search: "Search",
      edit: "Edit",
      delete: "Delete",
      actions: "Actions",
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
      password: {
        label: "Password",
        placeholder: "Password",
        required: "Password is required.",
      },
      passwordConfirmation: {
        label: "Password confirmation",
        placeholder: "Password confirmation",
        doesNotMatch: "Passwords do not match.",
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
      password: {
        label: "Password",
        placeholder: "Password",
        required: "Password is required.",
      },
      passwordConfirmation: {
        label: "Password confirmation",
        placeholder: "Password confirmation",
        doesNotMatch: "Passwords do not match.",
      },
    },
    accountSetup: {
      title: "Set up your Auditize account",
      success: "The setup of your user account is now complete.",
    },
    passwordReset: {
      title: "Reset your Auditize password",
      success: "Your password has been successfully updated.",
    },
    loginLink: "You can now log in by <1>clicking on this link</1>.",
  },
};
