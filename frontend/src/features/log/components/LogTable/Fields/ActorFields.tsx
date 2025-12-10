import { useTranslation } from "react-i18next";

import { Log } from "@/features/log/api";
import { ActorExtraFieldValue } from "@/features/log/components/CustomFieldValues";
import { useLogTranslator } from "@/features/log/components/LogTranslation";

import {
  getCustomField,
  InlineSearchParamLink,
  TableSearchParamChangeHandler,
} from "./FieldUtils";

export function ActorField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();

  return (
    log.actor && (
      <InlineSearchParamLink
        label={t("log.inlineFilter.field.actor")}
        onClick={() => onTableSearchParamChange("actorRef", log.actor!.ref)}
        anchorProps={{ fw: "600" }}
      >
        {log.actor.name}
      </InlineSearchParamLink>
    )
  );
}

export function ActorTypeField({
  log,
  repoId,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);

  return (
    log.actor && (
      <InlineSearchParamLink
        label={t("log.inlineFilter.field.actorType")}
        onClick={() => onTableSearchParamChange("actorType", log.actor!.type)}
      >
        {logTranslator("actor_type", log.actor.type)}
      </InlineSearchParamLink>
    )
  );
}

export function ActorNameField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();

  return (
    log.actor && (
      <InlineSearchParamLink
        label={t("log.inlineFilter.field.actorName")}
        onClick={() => onTableSearchParamChange("actorName", log.actor!.name)}
      >
        {log.actor.name}
      </InlineSearchParamLink>
    )
  );
}

export function ActorRefField({
  log,
  onTableSearchParamChange,
}: {
  log: Log;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();

  return (
    log.actor && (
      <InlineSearchParamLink
        label={t("log.inlineFilter.field.actorRef")}
        onClick={() => onTableSearchParamChange("actorRef", log.actor!.ref)}
      >
        {log.actor.ref}
      </InlineSearchParamLink>
    )
  );
}

export function ActorExtraField({
  log,
  repoId,
  fieldName,
  onTableSearchParamChange,
}: {
  log: Log;
  repoId: string;
  fieldName: string;
  onTableSearchParamChange: TableSearchParamChangeHandler;
}) {
  const { t } = useTranslation();
  const logTranslator = useLogTranslator(repoId);
  const field = getCustomField(log.actor?.extra, fieldName);
  if (!field) {
    return null;
  }

  return (
    <InlineSearchParamLink
      label={t("log.inlineFilter.field.actorExtraField", {
        field: logTranslator(
          "actor_extra_field_name",
          field.name,
        ).toLowerCase(),
      })}
      onClick={() =>
        onTableSearchParamChange(
          "actorExtra",
          new Map([[field.name, field.value]]),
        )
      }
    >
      <ActorExtraFieldValue repoId={repoId} field={field} />
    </InlineSearchParamLink>
  );
}
