import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

@Injectable({
  providedIn: 'root'
})
export class VmDetailsPopupService {

  private data: any = {}

  constructor(
    private service: Apollo
  ) { }
  
  updateEntity(data) {
    this.data = { ...data };
  }

  public getVm(pool_id: string = this.data.idPool, vm_id: string = this.data.vmActive, controller_address: string = this.data.controller_id, offset = 0): QueryRef<any, any> {
    return this.service.watchQuery({
      query: gql` query 
        pools(
          $pool_id: ShortString, 
          $vm_id: UUID, 
          $controller_address: UUID, 
          $offset: Int
        ){
          pool(
            pool_id: $pool_id
          ){
            vm(
              vm_id: $vm_id, 
              controller_id: 
              $controller_address
            ){
              id
              verbose_name
              description
              os_type
              os_version
              cpu_count
              memory_count
              tablet
              ha_enabled
              disastery_enabled
              guest_agent
              remote_access
              spice_stream
              user_power_state
              boot_type
              thin
              start_on_boot
              address
              status
              hostname
              domain_tags {
                colour
                verbose_name
              }
              parent_name
              resource_pool {
                id
                verbose_name
              }
              controller {
                id
                verbose_name
              }
              node {
                id
                verbose_name
              }
              assigned_users {
                id
                username
              }
              events(offset: $offset) {
                id
                event_type
                message
                description
                created
                user
                read_by {
                  id
                  username
                }
              }
              spice_connection {
                password
                host
                token
                connection_url
                connection_type
              }
              vnc_connection {
                password
                host
                token
                connection_url
                connection_type
              }
              count
              controller {
                id
              }
              backups {
                file_id
                vm_id
                filename
                datapool {
                  id
                  verbose_name
                }
                node {
                  id
                  verbose_name
                }
                assignment_type
                size
                status
              }
              vm_connection_data_list(offset: $offset) {
                id
                address
                port
                connection_type
                active
              }
              vm_connection_data_count
              vnc_connection {
                password
                host
                token
                connection_url
                connection_type
              }
              spice_connection {
                password
                host
                token
                connection_url
                connection_type
              }
            }
          }
        }
    `,
      variables: {
        method: 'GET',
        pool_id,
        vm_id,
        controller_address,
        offset
      }
    });
  }

  public getSpice(pool_id: string = this.data.idPool, vm_id: string = this.data.vmActive, controller_address: string = this.data.controller_id): QueryRef<any, any> {
    return this.service.watchQuery({
      query: gql`
                query pools($pool_id: ShortString, $vm_id: UUID, $controller_address: UUID) {
                    pool(pool_id: $pool_id) {
                        vm(vm_id: $vm_id, controller_id: $controller_address) {
                            id
                            spice_connection {
                                password
                                host
                                token
                                connection_url
                                connection_type
                            }
                        }
                    }
                }
            `,
      variables: {
        method: 'GET',
        pool_id,
        vm_id,
        controller_address
      }
    });
  }

  public getVnc(pool_id: string = this.data.idPool, vm_id: string = this.data.vmActive, controller_address: string = this.data.controller_id): QueryRef<any, any> {
    return this.service.watchQuery({
      query: gql`
                query pools($pool_id: ShortString, $vm_id: UUID, $controller_address: UUID) {
                    pool(pool_id: $pool_id) {
                        vm(vm_id: $vm_id, controller_id: $controller_address) {
                            id
                            vnc_connection {
                                password
                                host
                                token
                                connection_url
                                connection_type
                            }
                        }
                    }
                }
            `,
      variables: {
        method: 'GET',
        pool_id,
        vm_id,
        controller_address
      }
    });
  }

  public reserveVm(params: any) {
    return this.service.mutate<any>({
      mutation: gql`
            mutation pools($vm_id: UUID!, $reserve: Boolean!) {
                reserveVm(vm_id: $vm_id, reserve: $reserve){
                ok
            }
            }
        `,
      variables: {
        method: 'POST',
        ...params
      }
    });
  }

  public convertToTemplate(vm_id: string, data) {
    return this.service.mutate<any>({
      mutation: gql`
        mutation pools($verbose_name: ShortString!, $vm_id: UUID!,$controller_id: UUID!) {
            convertToTemplate(verbose_name: $verbose_name, vm_id: $vm_id, controller_id: $controller_id){
            ok
          }
        }
      `,
      variables: {
        method: 'POST',
        vm_id,
        ...data
      }
    });
  }

  public assignVmToUser(vm_id: string = this.data.vmActive, users: [string]) {
    return this.service.mutate<any>({
      mutation: gql`
                mutation pools($vm_id: ID!,$users: [UUID!]) {
                    assignVmToUser(vm_id: $vm_id, users: $users) {
                        ok
                    }
                }
            `,
      variables: {
        method: 'POST',
        vm_id,
        users
      }
    });
  }

  public freeVmFromUser(vm_id: string = this.data.vmActive, users: [string]) {
    return this.service.mutate<any>({
      mutation: gql`
                mutation pools($vm_id: ID!,$users: [UUID!]) {
                    freeVmFromUser(vm_id: $vm_id, users: $users) {
                        ok
                    }
                }
            `,
      variables: {
        method: 'POST',
        vm_id,
        users
      }
    });
  }

  public startVm(data) {
    return this.service.mutate<any>({
      mutation: gql`
                mutation pools(
                    $vm_id: UUID!
                ){
                    startVm(
                        vm_id: $vm_id
                    ){
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

  public suspendVm(data) {
    return this.service.mutate<any>({
      mutation: gql`
                mutation pools(
                    $vm_id: UUID!
                ){
                    suspendVm(
                        vm_id: $vm_id
                    ){
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

  public shutdownVm(data) {
    return this.service.mutate<any>({
      mutation: gql`
                mutation pools(
                    $vm_id: UUID!,
                    $force: Boolean
                ){
                    shutdownVm(
                        force: $force,
                        vm_id: $vm_id
                    ){
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

  public rebootVm(data) {
    return this.service.mutate<any>({
      mutation: gql`
                mutation pools(
                    $vm_id: UUID!,
                    $force: Boolean
                ){
                    rebootVm(
                        force: $force,
                        vm_id: $vm_id
                    ){
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

  public backupVm(data) {
    return this.service.mutate<any>({
      mutation: gql`
                mutation pools(
                    $vm_id: UUID!
                ){
                    backupVm(
                        vm_id: $vm_id
                    ){
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

  public restoreBackupVm(data) {
    return this.service.mutate<any>({
      mutation: gql`
                mutation pools(
                    $vm_id: UUID!
                    $file_id: UUID!
                    $node_id: UUID!
                    $datapool_id: UUID
                ){
                    restoreBackupVm(
                        vm_id: $vm_id
                        file_id: $file_id
                        node_id: $node_id
                        datapool_id: $datapool_id
                    ){
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

  public testDomainVm(vm_id: string) {
    return this.service.mutate<any>({
      mutation: gql`
                mutation pools(
                    $vm_id: UUID!
                ){
                    testDomainVm(vm_id: $vm_id) {
                        ok
                    }
                }
            `,
      variables: {
        method: 'POST',
        vm_id
      }
    });
  }

  public attachVeilUtils(data) {
    return this.service.mutate<any>({
      mutation: gql` mutation pools($id: UUID!, $controller_id: UUID!) {
                            attachVeilUtilsVm(vm_id: $id, controller_id: $controller_id) {
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

  public changeTemplate(data) {
    return this.service.mutate<any>({
      mutation: gql` mutation pools($id: UUID!, $controller_id: UUID!) {
                            changeTemplate(vm_id: $id, controller_id: $controller_id) {
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

  public addVmConnectionData(vm_id, data) {
    console.log(vm_id)
    return this.service.mutate<any>({
      mutation: gql`
        mutation pools (
          $vm_id: UUID!, 
          $active: Boolean!, 
          $address: ShortString!,
          $connection_type: PoolConnectionTypes!,
          $port: Int!)
        {
          addVmConnectionData(
            vm_id: $vm_id, 
            address: $address, 
            port: $port, 
            connection_type: $connection_type, 
            active: $active)
          {
            ok
          }
        }
    `,
      variables: {
        method: 'POST',
        vm_id,
        ...data
      }
    })
  }

  public removeVmConnectionData(data) {
    return this.service.mutate<any>({
      mutation: gql`
        mutation pools( 
          $id: UUID!
        ){
          removeVmConnectionData(
            id: $id
          ){
            ok
          }
        }
    `,
      variables: {
        method: 'POST',
        ...data
      }
    })
  }
}
