import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { IParams } from '@shared/types';

@Injectable()
export class GroupsService  {

    public paramsForGetUsers: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}

    public getGroups(queryset: any = {}): QueryRef<any, any> {
       return  this.service.watchQuery({
            query:  gql`
                query groups(
                    $limit: Int, 
                    $offset: Int
                    $ordering: ShortString,
                    $verbose_name: ShortString
                ){
                    count: group_count
                    groups(
                        limit: $limit,
                        offset: $offset,
                        verbose_name: $verbose_name,
                        ordering: $ordering
                    ){
                        id
                        verbose_name
                        description
                        assigned_users {
                            id
                        }
                    }
                }
            `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetUsers.nameSort,
                ...queryset
            }
        });
    }

    public getGroup(id: string, params?) {
        return this.service.watchQuery({
            query: gql` 
                query groups(
                    $id:UUID,
                    $offset: Int,
                    $limit: Int,
                    $username: ShortString
                ){
                    group(
                        id: $id
                    ){
                        id,
                        verbose_name,
                        description,
                        date_created,
                        date_updated,
                        assigned_permissions,
                        possible_permissions,
                        assigned_users_count,
                        assigned_users (
                            limit: $limit,
                            offset: $offset,
                            username: $username
                        ){
                            username
                            is_active
                            id
                        }
                        possible_users {
                            id
                            username
                        }
                        assigned_roles
                        possible_roles
                    }
                }
            `,
            variables: {
                method: 'GET',
                id,
                ...params
            }
        });
    }

    public getPossibleUsersFromGroup(id: string, params?) {
        return this.service.watchQuery({
            query: gql` 
                query groups(
                    $id:UUID,
                    $username: ShortString
                ){
                    group(
                        id: $id
                    ){
                        id,
                        possible_users(username: $username) {
                            id
                            username
                        }
                    }
                }
            `,
            variables: {
                method: 'GET',
                id,
                ...params
            }
        })
    }

    public getAssignedUsersFromGroup(id: string, params?) {
        return this.service.watchQuery({
            query: gql` 
                query groups(
                    $id:UUID,
                    $username: ShortString
                ){
                    group(
                        id: $id
                    ){
                        id,
                        assigned_users(username: $username) {
                            id
                            username
                        }
                    }
                }
            `,
            variables: {
                method: 'GET',
                id,
                ...params
            }
        })
    }

    public createGroup({verbose_name, description }) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation groups(
                    $verbose_name: ShortString!,
                    $description: ShortString){
                    createGroup(
                        description: $description,
                        verbose_name: $verbose_name
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                verbose_name,
                description
            }
        });
    }

    public removeGroup(id: string) {
      return this.service.mutate<any>({
          mutation: gql`
                          mutation groups(
                              $id: UUID!){
                              deleteGroup(
                                  id: $id
                              ){
                                  ok
                              }
                          }
          `,
          variables: {
              method: 'POST',
              id
          }
      });
    }

    public update({id}, {verbose_name, description}) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation groups($id: UUID!,$verbose_name: ShortString,
                                $description: ShortString) {
                                updateGroup(id: $id, verbose_name: $verbose_name,
                                    description: $description) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                id,
                verbose_name,
                description
            }
        });
    }

    public addGroupRole(roles: [], id: string) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation groups(
                                $roles: [Role!]!,
                                $id: UUID!){
                                addGroupRole(
                                    roles: $roles,
                                    id: $id
                                ){
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                roles,
                id
            }
        });
    }

    public removeGroupRole(roles: [], id: string) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation groups(
                                $roles: [Role!]!,
                                $id: UUID!){
                                removeGroupRole(
                                    roles: $roles,
                                    id: $id
                                ){
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                roles,
                id
            }
        });
    }

    public addUsers(users: [], id: string) {
      return this.service.mutate<any>({
          mutation: gql`
                          mutation groups(
                              $users: [UUID!]!,
                              $id: UUID!){
                              addGroupUsers(
                                  users: $users,
                                  id: $id
                              ){
                                  ok
                              }
                          }
          `,
          variables: {
              method: 'POST',
              users,
              id
          }
      });
  }

    public removeUsers(users: [], id: string) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation groups(
                                $users: [UUID!]!,
                                $id: UUID!){
                                removeGroupUsers(
                                    users: $users,
                                    id: $id
                                ){
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                users,
                id
            }
        });
    }

    public addPermission(id, permissions) {
        return this.service.mutate<any>({
            mutation: gql`
            mutation groups($id: UUID!, $permissions: [TkPermission!]!){
                addGroupPermission(id: $id, permissions: $permissions) {
                    ok
                }
            }`,
            variables: {
                method: 'POST',
                permissions,
                id
            }
        });
    }

    public removePermission(id, permissions) {
        return this.service.mutate<any>({
            mutation: gql`
            mutation groups($id: UUID!, $permissions: [TkPermission!]!){
                removeGroupPermission(id: $id, permissions: $permissions) {
                    ok
                }
            }`,
            variables: {
                method: 'POST',
                permissions,
                id
            }
        });
    }

}
