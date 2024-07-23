export default {
  navigation: {
    management: "Gestion",
    repositories: "Dépôts",
    users: "Utilisateurs",
    apikeys: "Clés d'API",
    logs: "Journaux",
    logi18nprofiles: "Traductions des journaux",
    preferences: "Préférences",
    logout: "Déconnexion",
  },
  language: {
    fr: "Français",
    en: "Anglais",
  },
  repo: {
    repo: "Dépôt",
    repos: "Dépôts",
    storage: "Stockage",
    lastLog: "Dernier journal",
    form: {
      name: {
        label: "Nom",
        placeholder: "Nom du dépôt",
        required: "Le nom du dépôt est requis.",
      },
      logI18nProfile: {
        label: "Traductions",
        placeholder: "Sélectionner un profil de traduction",
      },
      status: {
        label: "Statut",
        value: {
          enabled: "Activé",
          readonly: "Lecture seule",
          disabled: "Désactivé",
        },
      },
    },
    create: {
      title: "Créer un dépôt",
    },
    edit: {
      title: "Modifier le dépôt",
    },
    list: {
      title: "Dépôts",
      column: {
        name: "Nom",
        id: "Identifiant",
        status: "Statut",
        logs: "Journaux",
        storage: "Stockage",
        createdAt: "Date de création",
        lastLog: "Dernier journal",
      },
    },
    delete: {
      confirm:
        "Confirmez-vous la suppression du dépôt de journaux <1>{{name}}</1> ?",
    },
  },
  logi18nprofile: {
    logi18nprofile: "Profil de traduction des journaux",
    logi18nprofiles: "Profils de traduction des journaux",
    form: {
      name: {
        label: "Nom",
        placeholder: "Nom du profil",
        required: "Le nom du profil est requis.",
      },
      file: {
        label: "Fichier de traduction pour: {{lang}}",
        choose: "Sélectionner un fichier",
        configured: "Traduction configurée",
      },
    },
    create: {
      title: "Créer un profil de traduction des journaux",
    },
    edit: {
      title: "Modifier le profil de traduction des journaux",
    },
    list: {
      title: "Traduction des journaux",
      column: {
        name: "Nom",
        createdAt: "Date de création",
        langs: "Langues",
      },
    },
    delete: {
      confirm:
        "Confirmez-vous la suppression du profil de traduction des journaux <1>{{name}}</1> ?",
    },
  },
  user: {
    user: "Utilisateur",
    form: {
      firstName: {
        label: "Prénom",
        placeholder: "Prénom de l'utilisateur",
        required: "Le prénom est requis.",
      },
      lastName: {
        label: "Nom",
        placeholder: "Nom de l'utilisateur",
        required: "Le nom est requis.",
      },
      email: {
        label: "Email",
        placeholder: "Email de l'utilisateur",
        required: "L'email est invalide.",
      },
      language: {
        label: "Langue",
      },
    },
    list: {
      title: "Utilisateurs",
      column: {
        name: "Nom",
        email: "Email",
        permissions: "Permissions",
      },
    },
    create: {
      title: "Créer un utilisateur",
    },
    edit: {
      title: "Modifier l'utilisateur",
    },
    delete: {
      confirm:
        "Confirmez-vous la suppression de l'utilisateur <1>{{name}}</1> ?",
    },
  },
  apikey: {
    apikey: "Clé d'API",
    list: {
      title: "Clés d'API",
      column: {
        name: "Nom",
        permissions: "Permissions",
      },
    },
    form: {
      name: {
        label: "Nom",
        placeholder: "Nom de la clé",
        required: "Le nom de la clé est requis.",
      },
      key: {
        label: "Clé secrète",
        placeholder: {
          create:
            "Le secret sera affiché une fois que la clé aura été sauvegardée",
          update:
            "Vous pouvez générer un nouveau secret en cliquant sur le bouton rafraîchir",
        },
      },
    },
    create: {
      title: "Créer une clé d'API",
    },
    edit: {
      title: "Modifier la clé d'API",
    },
    delete: {
      confirm:
        "Confirmez-vous la suppression de la clé d'API <1>{{name}}</1> ?",
    },
  },
  log: {
    log: "Journal",
    logs: "Journaux",
    date: "Date",
    dateFrom: "À partir de",
    dateTo: "Jusqu'à",
    action: "Action",
    actionCategory: "Catégorie de l'action",
    actionType: "Type de l'action",
    actor: "Acteur",
    actorType: "Type d'acteur",
    actorName: "Nom de l'acteur",
    actorRef: "Référence de l'acteur",
    source: "Source",
    resource: "Ressource",
    resourceType: "Type de ressource",
    resourceName: "Nom de la ressource",
    resourceRef: "Référence de la ressource",
    details: "Détails",
    tag: "Étiquette",
    tags: "Étiquettes",
    tagType: "Type d'étiquette",
    tagTypes: "Types d'étiquettes",
    tagName: "Nom de l'étiquette",
    tagNames: "Noms des étiquettes",
    tagRef: "Référence de l'étiquette",
    tagRefs: "Références des étiquettes",
    attachment: "Pièce jointe",
    attachments: "Pièces jointes",
    attachmentType: "Type de pièce jointe",
    attachmentTypes: "Types de pièces jointes",
    attachmentMimeType: "Type MIME de la pièce jointe",
    attachmentMimeTypes: "Types MIME des pièces jointes",
    attachmentName: "Nom de la pièce jointe",
    attachmentNames: "Noms des pièces jointes",
    attachmentDescription: "Description de la pièce jointe",
    attachmentDescriptions: "Descriptions des pièces jointes",
    attachmentRef: "Référence de la pièce jointe",
    attachmentRefs: "Références des pièces jointes",
    node: "Arborescence",
    list: {
      columnSelector: {
        reset: "Réinitialiser les colonnes",
      },
      searchParams: {
        apply: "Appliquer",
        clear: "Effacer",
      },
      documentTitle: "Journaux",
    },
    view: {
      name: "Nom",
      type: "Type",
      ref: "Référence",
    },
    csv: {
      csv: "CSV",
      csvExportDefault: "Exporter en CSV (toutes les colonnes natives)",
      csvExportCurrent: "Exporter en CSV (colonnes sélectionnées)",
    },
    filter: {
      filter: "Filtre",
      filters: "Filtres",
      save: "Sauvegarder le filtre",
      update: "Mettre à jour le filtre actif",
      updateError: "Impossible de mettre à jour le filtre",
      updateSuccess: "Le filtre a été mis à jour",
      form: {
        name: {
          label: "Nom",
          placeholder: "Nom du filtre",
          required: "Le nom du filtre est requis.",
        },
      },
      create: {
        title: "Sauvegarder le filtre",
      },
      edit: {
        title: "Modifier le filtre",
      },
      delete: {
        confirm: "Confirmez-vous la suppression du filtre <1>{{name}}</1> ?",
      },
      list: {
        title: "Filtres",
        column: {
          name: "Nom",
        },
      },
    },
  },
  permission: {
    tab: {
      general: "Général",
      permissions: "Permissions",
    },
    read: "Lecture",
    write: "Écriture",
    superadmin: "Super administrateur (toutes les permissions)",
    management: "Gestion",
    repositories: "Dépôts",
    users: "Utilisateurs",
    apikeys: "Clés d'API",
    logs: "Journaux",
    allRepos: "Tous les dépôts",
    summary: {
      read: "lecture",
      write: "écriture",
      readwrite: "lecture/écriture",
      partial: "partiel",
      none: "Aucune",
      superadmin: "Super administrateur",
    },
  },
  common: {
    name: "Nom",
    id: "ID",
    status: "Statut",
    createdAt: "Date de création",
    copy: "Copier",
    copied: "Copié",
    enabled: "Activé",
    disabled: "Désactivé",
    readonly: "Lecture seule",
    error: "Erreur: {{error}}",
    save: "Enregistrer",
    cancel: "Annuler",
    confirm: "Confirmer",
    close: "Fermer",
    ok: "Ok",
    loading: "Chargement...",
    notCurrentlyAvailable: "Actuellement indisponible",
    errorModalTitle: "Une erreur est survenue",
  },
  resource: {
    list: {
      search: "Rechercher",
      edit: "Mod.",
      delete: "Suppr.",
      actions: "Actions",
    },
    edit: {
      save: "Enregistrer",
      cancel: "Annuler",
    },
    delete: {
      confirm: {
        title: "Confirmer la suppression",
      },
      cancel: "Annuler",
      delete: "Supprimer",
    },
  },
  accountSettings: {
    title: "Paramètres du compte",
    tab: {
      general: "Général",
    },
    form: {
      lang: {
        label: "Langue",
      },
    },
  },
  logout: {
    title: "Confirmer la déconnexion",
    confirm: "Souhaitez-vous vraiment vous déconnecter ?",
    expiration: "Votre session a expiré, vous devez vous reconnecter.",
  },
  login: {
    title: "Connexion",
    welcome: "Bienvenue sur Auditize",
    form: {
      email: {
        label: "Email",
        placeholder: "Votre email",
        invalid: "Email invalide",
      },
      password: {
        label: "Mot de passe",
        placeholder: "Votre mot de passe",
      },
    },
    signIn: "Connexion",
  },
};
