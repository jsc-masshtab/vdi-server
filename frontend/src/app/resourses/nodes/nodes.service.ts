import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class NodesService {

    constructor(private service: Apollo) {}

    public getAllNodes(cluster_id:string): QueryRef<any,any> {
        let controller_ip = JSON.parse(localStorage.getItem('controller'));
        return  this.service.watchQuery({
            query:  gql` query allNodes($controller_ip: String,$cluster_id: String) {
                            nodes(controller_ip: $controller_ip,cluster_id: $cluster_id) {
                                verbose_name
                                status
                                datacenter_id
                                datacenter_name
                                cpu_count
                                memory_count
                                management_ip
                                cluster {
                                    verbose_name
                                }
                            }
                        }
            
                    `,
            variables: {
                method: 'GET',
                controller_ip: controller_ip,
                cluster_id: cluster_id
            }
        }) 
    }

}
