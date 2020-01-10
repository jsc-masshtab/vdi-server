import { IParams } from '../../../../../types';
import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class AuthenticationDirectoryService  {

    public paramsForGetAuthenticationDirectory: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}

    public getAllAuthenticationDirectory(): QueryRef<any, any> {
       return  this.service.watchQuery({
           query: gql` query auth_dirs($ordering:String) {
                            auth_dirs(ordering: $ordering) {
                                verbose_name
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
                            $connection_type: ConnectionTypes,
                            $directory_type: DirectoryTypes,
                            $service_username: String,
                            $service_password: String,
                            $admin_server: String,
                            $subdomain_name: String,
                            $kdc_urls: [String],
                            $sso: Boolean,
                            ){
                                createAuthDir(
                                    domain_name :$domain_name,
                                    verbose_name: $verbose_name,
                                    directory_url :$directory_url,
                                    description :$description,
                                    connection_type :$connection_type,
                                    directory_type :$directory_type,
                                    service_username :$service_username,
                                    service_password :$service_password,
                                    admin_server :$admin_server,
                                    subdomain_name :$subdomain_name,
                                    kdc_urls :$kdc_urls,
                                    sso :$sso){
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
}
