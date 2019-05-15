import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class ClustersService  {

    constructor(private service: Apollo) {}

    public getAllClusters(): QueryRef<any,any> {
        let controller_ip = JSON.parse(localStorage.getItem('controller'));
        return  this.service.watchQuery({
            query:  gql` query allClusters($controller_ip: String) {
                            clusters(controller_ip: $controller_ip) {
                                id
                                verbose_name
                                nodes_count
                                status
                                cpu_count
                                memory_count
                                tags
                            }
                        }
            
                    `,
            variables: {
                method: 'GET',
                controller_ip: controller_ip
            }
        }) 
    }

}