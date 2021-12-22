import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { map } from 'rxjs/operators';

import { IParams } from '../../../shared/types';

@Injectable()
export class AuthenticationDirectoryService {

    public paramsForGetAuthenticationDirectory: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) { }

    public getAuthenticationDirectory(id: string): QueryRef<any, any> {
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
                                dc_str,
                                status,
                                sso,
                                assigned_ad_groups {
                                    id
                                    ad_search_cn
                                    ad_guid
                                    verbose_name
                                },
                                mappings {
                                    id
                                    verbose_name
                                    value_type
                                    values
                                    priority
                                    assigned_groups {
                                      id
                                      verbose_name
                                    }
                                    description
                                    status
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

    public getAuthenticationDirectoryGroups(id: string, group_name: string = ''): QueryRef<any, any> {
      return this.service.watchQuery({
        query: gql` query auth_dirs($id:UUID, $group_name:ShortString) {
                            auth_dir(id: $id) {
                                id
                                possible_ad_groups(group_name: $group_name) {
                                    ad_guid
                                    verbose_name
                                    ad_search_cn
                                }
                                assigned_ad_groups(group_name: $group_name) {
                                    id
                                    ad_search_cn
                                    ad_guid
                                    verbose_name
                                }
                            }
                        }
                    `,
        variables: {
          method: 'GET',
          id: `${id}`,
          group_name: `${group_name}`
        }
      });
    }

    // public getAuthenticationDirectoryGroupsMember(auth_dir_id: string, group_cn): QueryRef<any, any> {
    //     return this.service.watchQuery({
    //         query: gql` query auth_dirs($auth_dir_id: UUID, $group_cn: ShortString!) {
    //                         group_members(auth_dir_id: $auth_dir_id, group_cn: $group_cn) {
    //                             email
    //                             last_name
    //                             first_name
    //                             username
    //                         }
    //                     }
    //                 `,
    //         variables: {
    //             method: 'GET',
    //             auth_dir_id: `${auth_dir_id}`,
    //             group_cn: `${group_cn}`
    //         }
    //     });
    // }

    public getAllAuthenticationDirectory(): QueryRef<any, any> {
        return this.service.watchQuery({
            query: gql` query auth_dirs($ordering:ShortString) {
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
                                dc_str,
                                status,
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
                            $domain_name: ShortString!,
                            $dc_str: ShortString!,
                            $verbose_name: ShortString!,
                            $directory_url: ShortString!,
                            $directory_type: DirectoryTypes,
                            $description: ShortString,
                            $service_username: ShortString,
                            $service_password: ShortString
                        ){
                            createAuthDir(
                                domain_name :$domain_name,
                                dc_str: $dc_str,
                                verbose_name: $verbose_name,
                                directory_url :$directory_url,
                                directory_type: $directory_type,
                                description :$description,
                                service_username: $service_username,
                                service_password: $service_password,
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

    public syncOpenLDAPUsers(props) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation auth_dirs($id: UUID!) {
                    syncOpenLDAPUsers(auth_dir_id: $id, ou: "people") {
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
                mutation auth_dirs($id: UUID!, $description: ShortString,$verbose_name: ShortString!,
                                $value_type: ValueTypes, $groups: [UUID!]!,
                                $values: [ShortString!]!, $priority: Int) {
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

    public updateMapping(props, id: string, mapping_id: string) {
      return this.service.mutate<any>({
          mutation: gql`
              mutation auth_dirs($id: UUID!, $description: ShortString,$verbose_name: ShortString!,
                              $value_type: ValueTypes, $groups: [UUID!]!,
                              $values: [ShortString!]!, $priority: Int, $mapping_id: UUID!) {
                    editAuthDirMapping(id: $id, description: $description,verbose_name: $verbose_name,
                      value_type: $value_type, groups: $groups, values: $values, priority: $priority,
                      mapping_id: $mapping_id) {
                      ok
                  }
              }
          `,
          variables: {
              method: 'POST',
              ...props,
             id,
             mapping_id
          }
      });
    }

    public deleteMapping(id: string, mapping_id: string) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation auth_dirs($id: UUID!, $mapping_id: UUID!) {
                    deleteAuthDirMapping(id: $id, mapping_id: $mapping_id) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
            id,
            mapping_id
            }
        });
    }

    public syncAuthDirGroupUsers(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation auth_dirs(
                    $group_ad_cn: ShortString!,
                    $auth_dir_id: UUID!,
                    $group_ad_guid: UUID!,
                    $group_verbose_name: ShortString!){

                    syncAuthDirGroupUsers(
                        auth_dir_id: $auth_dir_id,
                        sync_data: {
                            group_ad_guid: $group_ad_guid
                            group_verbose_name: $group_verbose_name
                            group_ad_cn: $group_ad_cn
                        }
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

    public syncExistAuthDirGroupUsers(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation auth_dirs(
                    $auth_dir_id: UUID!,
                    $group_id: UUID!){

                    syncExistAuthDirGroupUsers(
                        auth_dir_id: $auth_dir_id,
                        group_id: $group_id
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


    public removeGroup(ad_guid: string) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation groups(
                    $ad_guid: UUID!){
                    deleteGroup(
                        ad_guid: $ad_guid
                    ){
                        ok
                    }
                }
          `,
            variables: {
                method: 'POST',
                ad_guid
            }
        });
    }

}


