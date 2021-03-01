import { IParams } from '../../../../../types';
import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

@Injectable()
export class UsersService  {

    public paramsForGetUsers: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}

    public getAllUsers(props: any = {}): QueryRef<any, any> {
       return  this.service.watchQuery({
           query: gql`
                query users(
                    $limit: Int,
                    $offset: Int,
                    $username: String,
                    $ordering:String,
                    $is_superuser: Boolean
                ){
                    count,
                    users(
                        ordering: $ordering
                        limit: $limit,
                        username: $username,
                        offset: $offset,
                        is_superuser: $is_superuser
                    ){
                        id,
                        username,
                        email,
                        last_name,
                        first_name,
                        date_joined,
                        date_updated,
                        last_login,
                        is_superuser,
                        is_active
                    }
                }
            `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetUsers.nameSort,
                ...props
            }
        });
    }

    public getUser(id): QueryRef<any, any> {
        return this.service.watchQuery({
            query: gql`
                query users($id:UUID!) {
                    user(id: $id) {
                        id,
                        username,
                        email,
                        last_name,
                        first_name,
                        date_joined,
                        date_updated,
                        last_login,
                        is_superuser,
                        is_active,
                        assigned_roles,
                        possible_roles,
                        assigned_permissions,
                        possible_permissions,
                        assigned_groups {
                            id
                            verbose_name
                        },
                        possible_groups {
                            id
                            verbose_name
                        }
                    }
                }
            `,
            variables: {
                method: 'GET',
                id: `${id}`
            }
        });
    }

    public createUser(props) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation users(
                    $username: String!,
                    $password: String!,
                    $email: String!,
                    $last_name: String!,
                    $first_name: String!,
                    $is_superuser: Boolean
                ){
                    createUser(
                        ${Object.keys(props).map((key) => {
                            return `${key} :$${key}`;
                        })}
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...props
            }
        });
    }

    public updateUser(params, fields) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation users(${params.args}) {
                    updateUser(${params.call}) {
                            ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...params.props,
                ...fields
            }
        });
    }

    public changeUserPassword(params, fields) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation users(${params.args}) {
                    changeUserPassword(${params.call}) {
                            ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...params.props,
                ...fields
            }
        });
    }

    public mutate(params) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation users(${params.args}) {
                    ${params.method}(${params.call}) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...params.props
            }
        });
    }

    public addGrop(id, groups) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation users(
                    $groups: [Group!]!,
                    $id: UUID!){
                    addUserGrop(
                        groups: $groups,
                        id: $id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                groups,
                id
            }
        });
    }

    public removeGroup(id, groups) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation users(
                    $roles: [Role!]!,
                    $id: UUID!){
                    addUserRole(
                        roles: $roles,
                        id: $id
                    ){
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                groups,
                id
            }
        });
    }

    public addRole(id, roles) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation users(
                    $roles: [Role!]!,
                    $id: UUID!){
                    addUserRole(
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

    public removeRole(id, roles) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation users(
                    $roles: [Role!]!,
                    $id: UUID!){
                    removeUserRole(
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

    public addPermission(id, permissions) {
        return this.service.mutate<any>({
            mutation: gql`
            mutation users($id: UUID!, $permissions: [TkPermission!]!){
                addUserPermission(id: $id, permissions: $permissions) {
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
            mutation users($id: UUID!, $permissions: [TkPermission!]!){
                removeUserPermission(id: $id, permissions: $permissions) {
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
