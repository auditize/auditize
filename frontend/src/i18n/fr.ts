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
    about: "À propos",
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
      retentionPeriod: {
        label: "Période de rétention",
        placeholder: "Période de rétention en jours",
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
        retentionPeriod: "Rétention",
        retentionPeriodValue: "{{days}}j",
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
    logi18nprofile: "Profil de traduction",
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
        authenticatedAt: "Dernière connexion",
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
    actorType: "Type de l'acteur",
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
    tagType: "Type de l'étiquette",
    tagTypes: "Types d'étiquettes",
    tagName: "Nom de l'étiquette",
    tagNames: "Noms des étiquettes",
    tagRef: "Référence de l'étiquette",
    tagRefs: "Références des étiquettes",
    hasAttachment: "Inclut une pièce jointe",
    attachment: "Pièce jointe",
    attachments: "Pièces jointes",
    attachmentType: "Type de pièce jointe",
    attachmentTypes: "Types de pièces jointes",
    attachmentMimeType: "Type MIME de la pièce jointe",
    attachmentMimeTypes: "Types MIME des pièces jointes",
    attachmentName: "Nom de la pièce jointe",
    attachmentNames: "Noms des pièces jointes",
    attachmentRef: "Référence de la pièce jointe",
    attachmentRefs: "Références des pièces jointes",
    downloadAttachment: "Télécharger la pièce jointe",
    entity: "Entité",
    list: {
      columnSelector: {
        tooltip: "Sélectionner les colonnes",
        reset: "Réinitialiser les colonnes",
      },
      searchParams: {
        apply: "Appliquer",
        clear: "Effacer",
        more: "Plus de paramètres",
      },
      documentTitle: "Journaux",
      noRepos: "Aucun dépôt de journaux n'a encore été créé",
      noResults: "Pas de résultats",
      loadMore: "Voir plus",
      untilMustBeGreaterThanSince:
        "La date de fin doit être postérieure à celle de début",
    },
    moreActions: "Plus d'actions",
    view: {
      name: "Nom",
      type: "Type",
      ref: "Référence",
    },
    csv: {
      csv: "CSV",
      csvExportDefault: "Exporter en CSV (colonnes par défaut)",
      csvExportCurrent: "Exporter en CSV (colonnes affichées)",
    },
    filter: {
      filter: "Filtre",
      filters: "Filtres",
      favoriteFilters: "Filtres favoris",
      save: "Sauvegarder le filtre",
      saveChanges: "Sauvegarder les modifications",
      saveAsNew: "Sauvegarder comme nouveau",
      updateError: "Impossible de mettre à jour le filtre",
      updateSuccess: "Le filtre a été mis à jour",
      manage: "Gérer les filtres",
      dirty: "Filtre modifié",
      setFavorite: "Ajouter le filtre aux favoris",
      unsetFavorite: "Retirer le filtre des favoris",
      clear: "Effacer le filtre",
      restore: "Restaurer le filtre",
      form: {
        name: {
          label: "Nom",
          placeholder: "Nom du filtre",
          required: "Le nom du filtre est requis.",
        },
        isFavorite: {
          label: "Favori",
          placeholder: "Inclure ce filtre dans les favoris",
        },
      },
      create: {
        title: "Sauvegarder le filtre",
      },
      edit: {
        title: "Modifier le filtre",
        tooltip: "Modifier le filtre",
      },
      delete: {
        confirm: "Confirmez-vous la suppression du filtre <1>{{name}}</1> ?",
      },
      list: {
        title: "Filtres",
        column: {
          name: "Nom",
        },
        apply: "Appliquer le filtre",
      },
    },
    inlineFilter: {
      filterOn: "Filtrer sur {{field}}",
      field: {
        actor: "cet acteur",
        actorType: "ce type d'acteur",
        actorRef: "cette référence d'acteur",
        actorName: "ce nom d'acteur",
        actorCustomField: "le champ {{field}} de cet acteur",
        actionType: "ce type d'action",
        actionCategory: "cette catégorie d'action",
        resource: "cette ressource",
        resourceType: "ce type de ressource",
        resourceRef: "cette référence de ressource",
        resourceName: "ce nom de ressource",
        resourceCustomField: "le champ {{field}} de cette ressource",
        tag: "cette étiquette",
        tagType: "ce type d'étiquette",
        tagName: "ce nom d'étiquette",
        tagRef: "cette référence d'étiquette",
        attachmentType: "ce type de pièce jointe",
        attachmentMimeType: "ce type MIME",
        attachmentName: "ce nom de pièce jointe",
        entity: "cette entité",
        sourceField: "ce champ {{field}}",
        detailField: "ce champ {{field}}",
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
    entities: "Entités",
    summary: {
      read: "lecture",
      write: "écriture",
      readwrite: "lecture/écriture",
      partial: "partiel",
      superadmin: "Super administrateur",
    },
  },
  common: {
    name: "Nom",
    id: "ID",
    status: "Statut",
    createdAt: "Date de création",
    copy: "Copier",
    copied: "Copié !",
    enabled: "Activé",
    disabled: "Désactivé",
    readonly: "Lecture seule",
    save: "Enregistrer",
    cancel: "Annuler",
    confirm: "Confirmer",
    submit: "Valider",
    delete: "Supprimer",
    close: "Fermer",
    clear: "Effacer",
    ok: "Ok",
    loading: "Chargement...",
    noData: "Aucune donnée",
    notCurrentlyAvailable: "Actuellement indisponible",
    unexpectedError: "Une erreur est survenue",
    send: "Envoyer",
    scrollToTop: "Revenir en haut",
    moreDetails: "Plus de détails",
    lessDetails: "Moins de détails",
    chooseAValue: "Choisissez une valeur",
    noResults: "Pas de résultats",
    passwordForm: {
      password: {
        label: "Mot de passe",
        placeholder: "Mot de passe",
        required: "Le mot de passe est requis.",
        tooShort: "Le mot de passe doit contenir au moins {{min}} caractères.",
      },
      passwordConfirmation: {
        label: "Confirmation du mot de passe",
        placeholder: "Confirmation du mot de passe",
        doesNotMatch: "Les mots de passe ne correspondent pas.",
      },
    },
    error: {
      error: "Erreur",
      details: "Erreur: {{error}}",
      unexpected: "Une erreur inattendue est survenue",
      401: "Erreur d'authentification",
      403: "Erreur: Cette opération n'est pas autorisée",
    },
  },
  CustomMultiSelect: {
    filterFields: "Filtrer",
  },
  resource: {
    list: {
      search: "Rechercher",
      delete: "Supprimer",
    },
    edit: {
      save: "Enregistrer",
      cancel: "Annuler",
    },
    delete: {
      confirm: {
        title: "Confirmer la suppression",
      },
    },
  },
  accountSettings: {
    title: "Paramètres du compte",
    tab: {
      general: "Général",
      password: "Mot de passe",
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
    invalidCredentials: "Email ou mot de passe incorrect. Veuillez réessayer.",
  },
  forgotPassword: {
    link: "Mot de passe oublié ?",
    title: "Demander un changement de mot de passe",
    description:
      "Veuillez saisir votre email pour recevoir un lien de réinitialisation de votre mot de passe.",
    emailSent:
      "Un email de réinitialisation de mot de passe vous a été envoyé (si l'adresse email indiquée est valide).",
    form: {
      email: {
        label: "Email",
        placeholder: "Votre email",
        invalid: "Email invalide",
      },
    },
  },
  passwordSetup: {
    form: {
      firstName: {
        label: "Prénom",
      },
      lastName: {
        label: "Nom",
      },
      email: {
        label: "Email",
      },
    },
    accountSetup: {
      title: "Finalisez la création de votre compte",
      success: "La création de votre compte a été finalisée avec succès.",
    },
    passwordReset: {
      title: "Réinitialisez votre mot de passe Auditize",
      success: "Votre mot de passe a été réinitialisé avec succès.",
    },
    loginLink:
      "Vous pouvez maintenant vous connecter en <1>cliquant sur ce lien</1>.",
    documentTitle: "Changement du mot de passe",
  },
  about: {
    title: "À propos",
    auditizeVersion: "Auditize version {{version}}",
  },
};
