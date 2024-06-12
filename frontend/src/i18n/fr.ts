export default {
  navigation: {
    management: "Gestion",
    repositories: "Dépôts",
    users: "Utilisateurs",
    apikeys: "Clés d'API",
    logs: "Journaux",
    preferences: "Préférences",
    logout: "Déconnexion",
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
      filter: {
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
