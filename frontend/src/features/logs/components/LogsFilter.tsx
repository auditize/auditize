import { useEffect, useReducer } from 'react';
import { Button, Group, TextInput, Space } from '@mantine/core';
import { useLocalStorage } from '@mantine/hooks';
import { getAllLogEventNames, getAllLogEventCategories, getAllLogActorTypes, getAllLogResourceTypes, getAllLogTagCategories, LogsFilterParams, buildEmptyLogsFilterParams } from '../api';
import { PaginatedSelector, PopoverForm, CustomDateTimePicker } from '@/components';
import { NodeSelector } from './NodeSelector';
import { labelize } from '@/utils/format';
import { getAllRepos } from '@/features/repos/api';

function EventCategorySelector({ category, onChange }: { category?: string; onChange: (value: string) => void; }) {
  return (
    <PaginatedSelector
      label="Event category"
      queryKey={['logEventCategory']} queryFn={getAllLogEventCategories}
      selectedItem={category} onChange={onChange}
      itemLabel={(item) => labelize(item)} itemValue={(item) => item}
    />
  );
}

function EventNameSelector(
  { name, category, onChange }: { name?: string; category?: string; onChange: (value: string) => void; }) {
  return (
    <PaginatedSelector
      label="Event name"
      queryKey={['logEventNames', category]} queryFn={() => getAllLogEventNames(category)}
      selectedItem={name} onChange={onChange}
      itemLabel={(item) => labelize(item)} itemValue={(item) => item}
    />
  );
}

function ActorTypeSelector({ type, onChange }: { type?: string; onChange: (value: string) => void; }) {
  return (
    <PaginatedSelector
      label="Actor type"
      queryKey={['logActorType']} queryFn={getAllLogActorTypes}
      selectedItem={type} onChange={onChange}
      itemLabel={(item) => labelize(item)} itemValue={(item) => item}
    />
  );
}

function ResourceTypeSelector({ type, onChange }: { type?: string; onChange: (value: string) => void; }) {
  return (
    <PaginatedSelector
      label="Resource type"
      queryKey={['logResourceType']} queryFn={getAllLogResourceTypes}
      selectedItem={type} onChange={onChange}
      itemLabel={(item) => labelize(item)} itemValue={(item) => item}
    />
  );
}

function TagCategorySelector({ category, onChange }: { category?: string; onChange: (value: string) => void; }) {
  return (
    <PaginatedSelector
      label="Tag category"
      queryKey={['logTagCategory']} queryFn={getAllLogTagCategories}
      selectedItem={category} onChange={onChange}
      itemLabel={(item) => labelize(item)} itemValue={(item) => item}
    />
  );
}

function RepoSelector({ repoId, onChange }: { repoId?: string; onChange: (value: string) => void; }) {
  const [defaultSelectedRepo, setDefaultSelectedRepo] = useLocalStorage({
    key: 'default-selected-repo'
  });

  useEffect(() => {
    if (repoId) {
      setDefaultSelectedRepo(repoId);
    }
  }, [repoId]);

  return (
    <PaginatedSelector
      label="Repository"
      queryKey={['repos']} queryFn={getAllRepos}
      selectedItem={repoId} clearable={false} onChange={onChange}
      onDataLoaded={(repos: Repo[]) => {
        // if no default repo or default repo is not in the list, select the first one (if any)
        if (!defaultSelectedRepo || !repos.find((repo) => repo.id === defaultSelectedRepo)) {
          if (repos.length > 0)
            onChange(repos[0].id);
        } else {
          onChange(defaultSelectedRepo);
        }
      }}
      itemLabel={(repo) => repo.name} itemValue={(repo) => repo.id}
    />
  );
}

interface SetParamAction {
  type: 'setParam';
  name: string;
  value: any;
}

interface ResetParamsAction {
  type: 'resetParams';
  params?: LogsFilterParams;
}

function filterParamsReducer(state: LogsFilterParams, action: SetParamAction | ResetParamsAction): LogsFilterParams {
  console.log("filterParamsReducer", action);
  switch (action.type) {
    case 'setParam':
      const update = { [action.name]: action.value };
      if (action.name === 'eventCategory')
        update['eventName'] = "";
      return { ...state, ...update };
    case 'resetParams':
      return action.params ? { ...buildEmptyLogsFilterParams(), ...action.params } : { ...buildEmptyLogsFilterParams() };
  }
}

export function LogsFilter({ params, onChange }: { params: LogsFilterParams; onChange: (filter: LogsFilterParams) => void; }) {
  const [editedParams, dispatch] = useReducer(filterParamsReducer, buildEmptyLogsFilterParams());
  useEffect(() => {
    dispatch({ type: 'resetParams', params });
  }, [params]);

  const changeParamHandler = (name: string) => (value: any) => dispatch({ type: 'setParam', name, value });
  const changeTextInputParamHandler = (name: string) => (e: React.ChangeEvent<HTMLInputElement>) => dispatch({ type: 'setParam', name, value: e.target.value });

  const hasDate = !!(editedParams.since || editedParams.until);
  const hasEvent = !!(editedParams.eventCategory || editedParams.eventName);
  const hasActor = !!(editedParams.actorType || editedParams.actorName);
  const hasResource = !!(editedParams.resourceType || editedParams.resourceName);
  const hasTag = !!(editedParams.tagCategory || editedParams.tagName || editedParams.tagId);
  const hasNode = !!editedParams.nodeId;
  const hasFilter = hasDate || hasEvent || hasActor || hasResource || hasTag || hasNode;

  return (
    <Group p="1rem">
      {/* Repository selector */}
      <RepoSelector repoId={editedParams.repoId} onChange={changeParamHandler("repoId")} />

      {/* Time criteria */}
      <PopoverForm title="Date" isFilled={hasDate}>
        <CustomDateTimePicker
          placeholder="From"
          value={editedParams.since}
          onChange={changeParamHandler("since")} />
        <CustomDateTimePicker
          placeholder="To"
          value={editedParams.until}
          onChange={changeParamHandler("until")}
          initToEndOfDay />
      </PopoverForm>

      {/* Event criteria */}
      <PopoverForm title="Event" isFilled={hasEvent}>
        <EventCategorySelector
          category={editedParams.eventCategory}
          onChange={changeParamHandler("eventCategory")} />
        <EventNameSelector
          name={editedParams.eventName} category={editedParams.eventCategory}
          onChange={changeParamHandler("eventName")} />
      </PopoverForm>

      {/* Actor criteria */}
      <PopoverForm title="Actor" isFilled={hasActor}>
        <ActorTypeSelector
          type={editedParams.actorType}
          onChange={changeParamHandler("actorType")} />
        <TextInput
          placeholder="Actor name"
          value={editedParams.actorName}
          onChange={changeTextInputParamHandler('actorName')}
          display={"flex"} />
      </PopoverForm>

      {/* Resource criteria */}
      <PopoverForm title="Resource" isFilled={hasResource}>
        <ResourceTypeSelector
          type={editedParams.resourceType}
          onChange={changeParamHandler("resourceType")} />
        <TextInput
          placeholder="Resource name"
          value={editedParams.resourceName}
          onChange={changeTextInputParamHandler('resourceName')}
          display={"flex"} />
      </PopoverForm>

      {/* Tag criteria */}
      <PopoverForm title="Tag" isFilled={hasTag}>
        <TagCategorySelector
          category={editedParams.tagCategory}
          onChange={changeParamHandler("tagCategory")} />
        <TextInput
          placeholder="Tag name"
          value={editedParams.tagName}
          onChange={changeTextInputParamHandler('tagName')}
          display="flex" />
        <TextInput
          placeholder="Tag id"
          value={editedParams.tagId}
          onChange={changeTextInputParamHandler('tagId')}
          display="flex" />
      </PopoverForm>

      {/* Node criteria */}
      <PopoverForm title="Node" isFilled={!!editedParams.nodeId}>
        <NodeSelector nodeId={editedParams.nodeId || null} onChange={changeParamHandler("nodeId")} />
      </PopoverForm>

      {/* Apply & clear buttons */}
      <Space w="l" />
      <Button onClick={() => onChange(editedParams)}>
        Apply
      </Button>
      <Button onClick={() => dispatch({ type: 'resetParams' })} disabled={!hasFilter} variant='default'>
        Clear
      </Button>
    </Group>
  );
}
