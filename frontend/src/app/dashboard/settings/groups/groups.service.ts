import { IParams } from '../../../../../types';
import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';



@Injectable()
export class GroupsService  {

    public paramsForGetUsers: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}

    public getGroups(): QueryRef<any, any> {
       return  this.service.watchQuery({
            query:  gql` query groups($ordering: String) {
                                groups(ordering: $ordering) {
                                    id
                                    verbose_name
                                    description
                                    users {
                                      id
                                    }
                                }
                            }
                    `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetUsers.nameSort
            }
        });
    }

    public getGroup(id: string): Observable<any> {
        return this.service.watchQuery({
            query: gql` query groups($id:UUID) {
                                group(id: $id) {
                                id,
                                verbose_name,
                                description,
                                date_created,
                                date_updated,
                                users {
                                    username
                                }
                                assigned_roles
                                possible_roles
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                id
            }
        }).valueChanges.pipe(map(data => data.data));
    }

    public createGroup({verbose_name, description }) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation groups(
                                $verbose_name: String!,
                                $description: String){
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

    public update({id}, {verbose_name, description}) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation groups($id: UUID!,$verbose_name: String,
                                $description: String) {
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

}
