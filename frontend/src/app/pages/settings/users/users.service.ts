import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { Subject } from 'rxjs';

import { IParams } from '../../../shared/types';

@Injectable()
export class UsersService  {

    portal = new Subject();
    portal$ = this.portal.asObservable();

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
                    $username: ShortString,
                    $ordering: ShortString,
                    $is_superuser: Boolean,
                    $is_active: Boolean
                ){
                    count(
                        is_superuser: $is_superuser,
                        is_active: $is_active
                    ),
                    users(
                        ordering: $ordering
                        limit: $limit,
                        username: $username,
                        offset: $offset,
                        is_superuser: $is_superuser,
                        is_active: $is_active
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
                        is_active,
                        two_factor,
                        by_ad,
                        local_password
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
                        two_factor,
                        by_ad,
                        local_password,
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
                    $username: ShortString!,
                    $password: ShortString!,
                    $email: ShortString!,
                    $last_name: ShortString!,
                    $first_name: ShortString!,
                    $groups: [GroupInput!]!,
                    $is_superuser: Boolean
                ){
                    createUser(
                        ${Object.keys(props).map((key) => `${key} :$${key}`)}
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

    public updateUser(params, fields?) {
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

    public deleteUser(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation users(
                    $id: UUID!){
                    deleteUser(id: $id) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...data
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

    public getGroups(queryset: any = {}): QueryRef<any, any> {
       return  this.service.watchQuery({
            query:  gql`
                query groups(
                    $ordering: ShortString,
                    $verbose_name: ShortString
                ){
                    groups(
                        verbose_name: $verbose_name,
                        ordering: $ordering
                    ){
                        id
                        verbose_name
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

    public generateUserQrcode(id): any {
        return this.service.mutate<any>({
            mutation: gql`
            mutation users($id: UUID!){
                generateUserQrcode(id: $id) {
                    qr_uri
                    secret
                }
            }`,
            variables: {
                method: 'POST',
                id
            }
        });
    }

    public getSettings(): QueryRef<any, any> {
        return this.service.watchQuery({
            query: gql`
                query settings {
                    settings {
                        PASSWORD_SECURITY_LEVEL
                    }
                }
            `,
            variables: {
                method: 'GET'
            },
            fetchPolicy: 'network-only'
        });
    }

    public setSettings(_, data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation settings($PASSWORD_SECURITY_LEVEL: PassSecLevel) {
                    changeSettings(
                        PASSWORD_SECURITY_LEVEL: $PASSWORD_SECURITY_LEVEL
                    ) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }
}
