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

    public getGroups(queryset): QueryRef<any, any> {
       return  this.service.watchQuery({
            query:  gql`
                query groups(
                    $ordering: String,
                    $verbose_name: String
                ){
                    groups(
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

    public getGroup(id: string): Observable<any> {
        return this.service.watchQuery({
            query: gql` query groups($id:UUID) {
                                group(id: $id) {
                                id,
                                verbose_name,
                                description,
                                date_created,
                                date_updated,
                                assigned_users {
                                  username
                                  is_active
                                  id
                                }
                                possible_users{
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

}
