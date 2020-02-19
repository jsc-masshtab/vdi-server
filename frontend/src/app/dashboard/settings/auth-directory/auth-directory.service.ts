import { IParams } from '../../../../../types';
import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

@Injectable()
export class AuthenticationDirectoryService {

    public paramsForGetAuthenticationDirectory: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) { }

    public getAuthenticationDirectory(id: string): Observable<any> {
        return this.service.watchQuery({
            query: gql` query auth_dirs($id:UUID) {
                            auth_dir(id: $id) {
                                id,
                                domain_name,
                                verbose_name,
                                directory_url,
                                description,
                                connection_type,
                                directory_type,
                                service_username,
                                service_password,
                                admin_server,
                                subdomain_name,
                                kdc_urls,
                                sso
                                mappings {
                                    id
                                    verbose_name
                                    value_type
                                    values
                                    priority
                                }
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                id: `${id}`
            }
        }).valueChanges.pipe(map(data => data.data));
    }

    public getAllAuthenticationDirectory(): QueryRef<any, any> {
        return this.service.watchQuery({
            query: gql` query auth_dirs($ordering:String) {
                            auth_dirs(ordering: $ordering) {
                                id,
                                domain_name,
                                verbose_name,
                                directory_url,
                                description,
                                connection_type,
                                directory_type,
                                service_username,
                                service_password,
                                admin_server,
                                subdomain_name,
                                kdc_urls,
                                sso
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetAuthenticationDirectory.nameSort
            }
        });
    }

    public createAuthDir(props) {
        return this.service.mutate<any>({
            mutation: gql`
                        mutation auth_dirs(
                            $domain_name: String!,
                            $verbose_name: String!,
                            $directory_url: String!,
                            $description: String,
                        ){
                            createAuthDir(
                                domain_name :$domain_name,
                                verbose_name: $verbose_name,
                                directory_url :$directory_url,
                                description :$description
                            ){
                                ok,
                                auth_dir {
                                    id
                                }
                            }
                        }
            `,
            variables: {
                method: 'POST',
                ...props
            }
        });
    }

    public updateAuthenticationDirectory(params, fields) {

        if (fields['kdc_urls']) {
            fields['kdc_urls'] = fields['kdc_urls'].split(',');
        }

        return this.service.mutate<any>({
            mutation: gql`
                            mutation auth_dirs(${params.args}) {
                                updateAuthDir(${params.call}) {
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

    public testAuthenticationDirectory(props) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation auth_dirs($id: UUID!) {
                    testAuthDir(id: $id) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...props
            }
        }).pipe(map(data => data.data));
    }

    public deleteAuthDir(props) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation auth_dirs($id: UUID!) {
                    deleteAuthDir(id: $id) {
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

    public getGroups(): QueryRef<any, any> {
        return  this.service.watchQuery({
             query:  gql` query groups {
                                groups {
                                    id
                                    verbose_name
                                }
                             }
                     `,
             variables: {
                method: 'GET'
             }
        });
     }

     public addAuthDirMapping(props, id: string) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation auth_dirs($id: UUID!, $description: String,$verbose_name: String!,
                                $value_type: ValueTypes, $groups: [UUID!]!,
                                $values: [String!]!, $priority: Int) {
                    addAuthDirMapping(id: $id, description: $description,verbose_name: $verbose_name,
                        value_type: $value_type, groups: $groups, values: $values, priority: $priority) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...props,
                id
            }
        });
    }
}