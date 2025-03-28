import { Aws, StackProps, RemovalPolicy, Duration } from 'aws-cdk-lib';
import {
  AccountRecovery,
  CfnUserPoolGroup,
  CfnUserPoolUser,
  CfnUserPoolUserToGroupAttachment,
  OAuthScope,
  UserPool,
  UserPoolDomain,
  VerificationEmailStyle,
} from 'aws-cdk-lib/aws-cognito';
import { Construct } from 'constructs';
import { Constants } from '../shared/constants';

export interface UserProps extends StackProps {
  readonly deployRegion: string;
  readonly adminEmail: string;
  readonly callbackUrls: string[];
  readonly logoutUrls: string[];
  readonly userPoolName?: string;
  readonly domainPrefix?: string;
}

export interface UserConstructOutputs {
  oidcIssuer: string;
  oidcClientId: string;
  oidcLogoutUrl: string;
  userPoolId: string;
  oidcDomain: string;
  oidcRegion: string;
}

export class UserConstruct extends Construct implements UserConstructOutputs {
  public oidcIssuer!: string;
  public oidcClientId!: string;
  public oidcLogoutUrl!: string;
  public userPoolId!: string;
  public oidcDomain!: string;
  public oidcRegion!: string;

  constructor(scope: Construct, id: string, props: UserProps) {
    super(scope, id);
    const userPoolName = props.userPoolName || `${Constants.SOLUTION_NAME}_UserPool`;
    const domainPrefix = props.domainPrefix || `${Constants.SOLUTION_NAME.toLowerCase()}-${Aws.ACCOUNT_ID}`;
    this.setupCognitoResources(props, userPoolName, domainPrefix);
  }

  private setupCognitoResources(props: UserProps, userPoolName: string, domainPrefix: string) {
    const cognitoUserPool = new UserPool(this, 'UserPool', {
      userPoolName: userPoolName,
      selfSignUpEnabled: false,
      signInCaseSensitive: false,
      accountRecovery: AccountRecovery.EMAIL_ONLY,
      removalPolicy: RemovalPolicy.DESTROY,
      signInAliases: {
        email: true,
      },
      userVerification: {
        emailStyle: VerificationEmailStyle.LINK,
      },
      // advancedSecurityMode: AdvancedSecurityMode.ENFORCED,
      passwordPolicy: {
        minLength: 8,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      userInvitation: {
        emailSubject: 'Welcome to use AI Customer Service',
        emailBody: 'Hello {username}, your temporary password is {####}',
      },
    });

    const userPoolDomain = new UserPoolDomain(this, 'UserPoolDomain', {
      userPool: cognitoUserPool,
      cognitoDomain: {
        domainPrefix: domainPrefix,
      },
    });

    const userPoolClient = cognitoUserPool.addClient('UserPoolClient', {
      userPoolClientName: Constants.SOLUTION_NAME,
      authFlows: {
        userSrp: true,
        userPassword: true,
      },
      oAuth: {
        callbackUrls: props.callbackUrls,
        logoutUrls: props.logoutUrls,
        scopes: [OAuthScope.OPENID, OAuthScope.PROFILE, OAuthScope.EMAIL],
      },
      accessTokenValidity: Duration.days(1),
      idTokenValidity: Duration.days(1),
      refreshTokenValidity: Duration.days(7),
    });

    const adminUser = new CfnUserPoolUser(this, 'AdminUser', {
      userPoolId: cognitoUserPool.userPoolId,
      username: props.adminEmail,
      userAttributes: [
        {
          name: 'email',
          value: props.adminEmail,
        },
        {
          name: 'email_verified',
          value: 'true',
        },
      ],
    });

    const adminGroup = new CfnUserPoolGroup(this, 'AdminGroup', {
      userPoolId: cognitoUserPool.userPoolId,
      groupName: 'Admin',
      description: 'Admin group',
    });

    const grpupAttachment = new CfnUserPoolUserToGroupAttachment(this, 'UserGroupAttachment', {
      userPoolId: cognitoUserPool.userPoolId,
      groupName: adminGroup.groupName!,
      username: adminUser.username!,
    });
    grpupAttachment.addDependency(adminUser);
    grpupAttachment.addDependency(adminGroup);

    this.oidcIssuer = `https://cognito-idp.${props.deployRegion}.amazonaws.com/${cognitoUserPool.userPoolId}`;
    this.oidcClientId = userPoolClient.userPoolClientId;
    this.oidcLogoutUrl = `${userPoolDomain.baseUrl()}/logout`;
    this.userPoolId = cognitoUserPool.userPoolId;
    this.oidcDomain = userPoolDomain.baseUrl();
    this.oidcRegion = props.deployRegion;
  }
}
